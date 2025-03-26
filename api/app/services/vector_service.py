from typing import List, Optional, Dict, Any
import os
import uuid
import json
import numpy as np
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging

# Assurez-vous que l'import LLMService est correct
from app.llm.llm_factory import LLMService
from app.models.analysis import Precedent

logger = logging.getLogger(__name__)

class VectorService:
    """Service pour la gestion de la base de données vectorielle (Qdrant)."""
    
    def __init__(self):
        # Connexion à Qdrant
        qdrant_uri = os.getenv("QDRANT_URI", "http://qdrant:6333")
        self.client = QdrantClient(url=qdrant_uri)
        
        # Nom de la collection pour les précédents juridiques
        self.collection_name = "legal_precedents"
        
        # Dimensionnalité des vecteurs
        self.vector_size = 768
        
        # Initialiser la collection si elle n'existe pas
        self._init_collection()
        
    def _init_collection(self):
        """Initialise la collection Qdrant si elle n'existe pas."""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            # Créer la collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
    
    async def _vectorize(self, text: str) -> List[float]:
        """
        Convertit un texte en embedding vectoriel via LLMService.
        En cas d'erreur, renvoie un vecteur aléatoire (fallback).
        """
        try:
            llm_service = LLMService()
            # IMPORTANT: on "await" l'appel pour obtenir réellement la liste de floats
            embedding = await llm_service.get_embedding(text)
            return embedding
        except Exception as e:
            logger.error(f"Erreur lors de la vectorisation: {str(e)}", exc_info=True)
            # Fallback : renvoyer un vecteur aléatoire pour éviter l'échec total
            import hashlib
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (10 ** 8)
            np.random.seed(seed)
            return np.random.random(self.vector_size).tolist()
        
    async def search_precedents(
        self,
        query: str,
        limit: int = 10
    ) -> List[Precedent]:
        """
        Recherche des précédents juridiques similaires dans Qdrant.
        Retourne une liste de Precedent.
        """
        # 1) Vectoriser la requête (avec await)
        query_vector = await self._vectorize(query)
        
        # 2) Appeler Qdrant pour la similarité
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,  # liste[float]
            limit=limit
        )
        
        # 3) Convertir en liste de Precedent
        precedents = []
        for result in search_result:
            payload = result.payload or {}
            precedent = Precedent(
                title=payload.get("title", ""),
                description=payload.get("description", ""),
                type=payload.get("type", ""),
                relevance=payload.get("relevance", ""),
                source=payload.get("source"),
                similarity_score=result.score
            )
            precedents.append(precedent)
        return precedents
    
    async def get_precedent(self, precedent_id: str) -> Optional[Precedent]:
        """
        Récupère un précédent juridique par son ID dans Qdrant.
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[precedent_id]
            )
            if not points:
                return None
            
            point = points[0]
            payload = point.payload or {}
            return Precedent(
                title=payload.get("title", ""),
                description=payload.get("description", ""),
                type=payload.get("type", ""),
                relevance=payload.get("relevance", ""),
                source=payload.get("source"),
                similarity_score=1.0  # On met 1.0 par défaut (récupération directe)
            )
        except Exception as e:
            logger.error(f"Erreur lors de get_precedent: {str(e)}", exc_info=True)
            return None
    
    async def add_precedent(
        self,
        title: str,
        description: str,
        precedent_type: str,
        relevance: str,
        source: Optional[str] = None
    ) -> str:
        """
        Ajoute un nouveau précédent juridique à la base vectorielle et renvoie son ID.
        """
        # Générer un ID
        precedent_id = str(uuid.uuid4())
        
        # Création du payload
        payload = {
            "title": title,
            "description": description,
            "type": precedent_type,
            "relevance": relevance,
            "created_at": datetime.now().isoformat()
        }
        if source:
            payload["source"] = source
        
        # Vectoriser la description
        vector = await self._vectorize(description)
        
        # Upsert dans Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=precedent_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        return precedent_id
    
    async def seed_precedents(self, precedents_file: str) -> int:
        """
        Charge plusieurs précédents depuis un fichier JSON et les insère dans Qdrant.
        """
        if not os.path.exists(precedents_file):
            return 0
        
        with open(precedents_file, 'r', encoding='utf-8') as f:
            precedents_data = json.load(f)
            
        count = 0
        for precedent in precedents_data:
            await self.add_precedent(
                title=precedent["title"],
                description=precedent["description"],
                precedent_type=precedent["type"],
                relevance=precedent["relevance"],
                source=precedent.get("source")
            )
            count += 1
        return count

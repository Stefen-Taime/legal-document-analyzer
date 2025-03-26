#!/usr/bin/env python3

import os
import sys
import json
import asyncio
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
QDRANT_HOST = os.getenv("QDRANT_URI", "http://qdrant:6333")
COLLECTION_NAME = "legal_precedents"
DATA_FILE = "/app/data/precedents.json"

async def main():
    print(f"Connexion à Qdrant sur {QDRANT_HOST}...")
    client = QdrantClient(url=QDRANT_HOST)
    
    # Vérifier si la collection existe déjà
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    # Charger le modèle de vectorisation
    print("Chargement du modèle de vectorisation...")
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    vector_size = model.get_sentence_embedding_dimension()
    
    # Créer la collection si elle n'existe pas
    if COLLECTION_NAME not in collection_names:
        print(f"Création de la collection {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )
    else:
        print(f"La collection {COLLECTION_NAME} existe déjà.")
    
    # Charger les données des précédents juridiques
    print(f"Chargement des données depuis {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        precedents = json.load(f)
    
    # Vectoriser et ajouter les précédents à Qdrant
    print(f"Ajout de {len(precedents)} précédents juridiques à Qdrant...")
    
    points = []
    for i, precedent in enumerate(precedents):
        # Vectoriser la description
        vector = model.encode(precedent["description"]).tolist()
        
        # Créer le point
        points.append(
            models.PointStruct(
                id=i,
                vector=vector,
                payload={
                    "title": precedent["title"],
                    "description": precedent["description"],
                    "type": precedent["type"],
                    "relevance": precedent["relevance"],
                    "source": precedent.get("source", "")
                }
            )
        )
    
    # Ajouter les points à Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    print(f"Initialisation terminée! {len(precedents)} précédents juridiques ajoutés à Qdrant.")

if __name__ == "__main__":
    asyncio.run(main())

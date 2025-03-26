from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from app.models.document import Document, DocumentType, DocumentStatus

class DocumentService:
    """Service pour la gestion des documents juridiques"""
    
    def __init__(self):
        # Récupérer les variables d'environnement pour MongoDB
        mongodb_user = os.getenv("MONGODB_USER", "admin")
        mongodb_password = os.getenv("MONGODB_PASSWORD", "password_securise")
        mongodb_host = os.getenv("MONGODB_HOST", "mongodb")
        mongodb_port = os.getenv("MONGODB_PORT", "27017")
        mongodb_db = os.getenv("MONGODB_DB", "legal_analyzer")
        
        # Construire l'URI avec authentification
        mongodb_uri = f"mongodb://{mongodb_user}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_db}?authSource=admin"
        
        # Connexion à MongoDB avec l'URI authentifié
        self.client = AsyncIOMotorClient(mongodb_uri)
        self.db = self.client[mongodb_db]
        self.collection = self.db.documents
        
    async def create_document(
        self,
        document_id: str,
        filename: str,
        content_type: str,
        size: int,
        file_path: str,
        document_type: Optional[DocumentType] = None
    ) -> Document:
        """Crée un nouveau document dans la base de données"""
        
        document = Document(
            id=document_id,
            filename=filename,
            content_type=content_type,
            size=size,
            file_path=file_path,
            document_type=document_type,
            status=DocumentStatus.PENDING
        )
        
        # Convertir le modèle Pydantic en dictionnaire
        document_dict = document.dict()
        
        # Insérer dans MongoDB
        try:
            await self.collection.insert_one(document_dict)
        except DuplicateKeyError:
            # Si le document existe déjà, le mettre à jour
            await self.collection.replace_one({"id": document_id}, document_dict)
            
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Récupère un document par son ID"""
        
        document_dict = await self.collection.find_one({"id": document_id})
        
        if not document_dict:
            return None
            
        return Document(**document_dict)
    
    async def update_document_type(
        self,
        document_id: str,
        document_type: DocumentType
    ) -> Optional[Document]:
        """Met à jour le type d'un document"""
        
        # Vérifier que le document existe
        document = await self.get_document(document_id)
        
        if not document:
            return None
            
        # Mettre à jour le type et la date de mise à jour
        document.document_type = document_type
        document.updated_at = datetime.now()
        
        # Mettre à jour dans MongoDB
        await self.collection.update_one(
            {"id": document_id},
            {"$set": {
                "document_type": document_type,
                "updated_at": document.updated_at
            }}
        )
        
        return document
    
    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus
    ) -> Optional[Document]:
        """Met à jour le statut d'un document"""
        
        # Vérifier que le document existe
        document = await self.get_document(document_id)
        
        if not document:
            return None
            
        # Mettre à jour le statut et la date de mise à jour
        document.status = status
        document.updated_at = datetime.now()
        
        # Mettre à jour dans MongoDB
        await self.collection.update_one(
            {"id": document_id},
            {"$set": {
                "status": status,
                "updated_at": document.updated_at
            }}
        )
        
        return document
    
    async def update_document_text_content(
        self,
        document_id: str,
        text_content: str
    ) -> Optional[Document]:
        """Met à jour le contenu texte d'un document"""
        
        # Vérifier que le document existe
        document = await self.get_document(document_id)
        
        if not document:
            return None
            
        # Mettre à jour le contenu texte et la date de mise à jour
        document.text_content = text_content
        document.updated_at = datetime.now()
        
        # Mettre à jour dans MongoDB
        await self.collection.update_one(
            {"id": document_id},
            {"$set": {
                "text_content": text_content,
                "updated_at": document.updated_at
            }}
        )
        
        return document
    
    async def delete_document(self, document_id: str) -> bool:
        """Supprime un document"""
        
        # Vérifier que le document existe
        document = await self.get_document(document_id)
        
        if not document:
            return False
            
        # Supprimer le fichier
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            
        # Supprimer de MongoDB
        result = await self.collection.delete_one({"id": document_id})
        
        return result.deleted_count > 0
    
    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Liste tous les documents"""
        
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        documents = []
        
        async for document_dict in cursor:
            documents.append(Document(**document_dict))
            
        return documents
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class DocumentType(str, Enum):
    EMPLOYMENT = "employment"
    SERVICE = "service"
    PARTNERSHIP = "partnership"
    NDA = "nda"
    OTHER = "other"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """Modèle de base pour un document juridique"""
    filename: str
    content_type: str
    size: int
    document_type: Optional[DocumentType] = None


class DocumentCreate(DocumentBase):
    """Modèle pour la création d'un document"""
    pass


class Document(DocumentBase):
    """Modèle complet d'un document juridique"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.PENDING
    file_path: str
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "filename": "contrat_travail.pdf",
                "content_type": "application/pdf",
                "size": 1024567,
                "document_type": "employment",
                "created_at": "2025-03-25T12:00:00",
                "updated_at": "2025-03-25T12:05:00",
                "status": "processed",
                "file_path": "/app/uploads/f47ac10b-58cc-4372-a567-0e02b2c3d479.pdf",
                "text_content": "Contrat de travail entre...",
                "metadata": {
                    "page_count": 12,
                    "language": "fr"
                }
            }
        }


class DocumentInDB(Document):
    """Modèle pour la représentation en base de données"""
    pass


class DocumentResponse(BaseModel):
    """Modèle pour la réponse API"""
    id: str
    filename: str
    document_type: Optional[DocumentType] = None
    created_at: datetime
    status: DocumentStatus
    size: int

    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "filename": "contrat_travail.pdf",
                "document_type": "employment",
                "created_at": "2025-03-25T12:00:00",
                "status": "processed",
                "size": 1024567
            }
        }

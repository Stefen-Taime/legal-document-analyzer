from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(int, Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ClauseType(str, Enum):
    OBLIGATION = "obligation"
    RESTRICTION = "restriction"
    RIGHT = "right"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    LIABILITY = "liability"
    PAYMENT = "payment"
    DURATION = "duration"
    OTHER = "other"


class Clause(BaseModel):
    """Modèle pour une clause extraite d'un document"""
    title: str
    content: str
    type: ClauseType
    risk_level: RiskLevel
    analysis: str
    page: Optional[int] = None
    position: Optional[Dict[str, Any]] = None
    
    
class AnalysisRequest(BaseModel):
    """Modèle pour la requête d'analyse"""
    document_id: str
    document_type: Optional[str] = None    


class Recommendation(BaseModel):
    """Modèle pour une recommandation basée sur l'analyse"""
    title: str
    description: str
    priority: Priority
    suggested_text: Optional[str] = None
    related_clauses: List[str] = Field(default_factory=list)


class Risk(BaseModel):
    """Modèle pour un risque juridique identifié"""
    title: str
    description: str
    level: RiskLevel
    impact: str
    mitigation: Optional[str] = None


class Precedent(BaseModel):
    """Modèle pour un précédent juridique similaire"""
    title: str
    description: str
    type: str
    relevance: str
    source: Optional[str] = None
    similarity_score: float


class AnalysisResults(BaseModel):
    """Modèle pour les résultats d'une analyse"""
    clauses: List[Clause] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    precedents: List[Precedent] = Field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisBase(BaseModel):
    """Modèle de base pour une analyse de document"""
    document_id: str
    document_type: str


class AnalysisCreate(AnalysisBase):
    """Modèle pour la création d'une analyse"""
    pass


class Analysis(AnalysisBase):
    """Modèle complet d'une analyse de document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: AnalysisStatus = AnalysisStatus.PENDING
    results: Optional[AnalysisResults] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Ajoutez cette ligne

    class Config:
        schema_extra = {
            "example": {
                "id": "a47ac10b-58cc-4372-a567-0e02b2c3d479",
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "document_type": "employment",
                "created_at": "2025-03-25T12:00:00",
                "updated_at": "2025-03-25T12:15:00",
                "status": "completed",
                "processing_time": 45.2,
                "results": {
                    "clauses": [
                        {
                            "title": "Clause de non-concurrence",
                            "content": "Le salarié s'engage à ne pas...",
                            "type": "restriction",
                            "risk_level": 4,
                            "analysis": "Cette clause est particulièrement restrictive...",
                            "page": 3
                        }
                    ],
                    "recommendations": [
                        {
                            "title": "Modifier la clause de non-concurrence",
                            "description": "La clause actuelle est trop restrictive...",
                            "priority": 3,
                            "suggested_text": "Le salarié s'engage à ne pas exercer..."
                        }
                    ],
                    "risks": [
                        {
                            "title": "Risque de nullité de la clause",
                            "description": "La clause pourrait être jugée nulle...",
                            "level": 4,
                            "impact": "Invalidation de la protection..."
                        }
                    ],
                    "precedents": [
                        {
                            "title": "Arrêt Cour de Cassation 2023",
                            "description": "Dans cette affaire similaire...",
                            "type": "jurisprudence",
                            "relevance": "Très pertinent pour la clause de non-concurrence",
                            "similarity_score": 0.87
                        }
                    ],
                    "summary": "Ce contrat de travail présente plusieurs risques..."
                }
            }
        }


class AnalysisInDB(Analysis):
    """Modèle pour la représentation en base de données"""
    pass


class AnalysisResponse(BaseModel):
    """Modèle pour la réponse API"""
    id: str
    document_id: str
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    processing_time: Optional[float] = None
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "a47ac10b-58cc-4372-a567-0e02b2c3d479",
                "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "completed",
                "created_at": "2025-03-25T12:00:00",
                "updated_at": "2025-03-25T12:15:00",
                "processing_time": 45.2
            }
        }


class AnalysisStatusResponse(BaseModel):
    """Modèle pour la réponse de statut d'une analyse"""
    id: str
    status: AnalysisStatus
    progress: Optional[float] = None
    error: Optional[str] = None
    results: Optional[AnalysisResults] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "a47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "in_progress",
                "progress": 0.65
            }
        }

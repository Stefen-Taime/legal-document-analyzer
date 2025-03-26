from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.models.document import Document, DocumentResponse, DocumentType, DocumentStatus
from app.services.document_service import DocumentService

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends()
):
    """
    Télécharge un document juridique pour analyse
    """
    try:
        # Vérifier le type de fichier
        allowed_content_types = [
            "application/pdf", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain"
        ]
        
        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=400, 
                detail="Type de fichier non supporté. Formats acceptés: PDF, DOCX, DOC, TXT"
            )
        
        # Vérifier la taille du fichier (10 Mo max)
        max_size = 10 * 1024 * 1024  # 10 Mo en octets
        file_size = 0
        
        # Lire le contenu du fichier pour obtenir sa taille
        content = await file.read()
        file_size = len(content)
        
        # Revenir au début du fichier pour le traitement ultérieur
        await file.seek(0)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Taille du fichier trop importante. Maximum: 10 Mo"
            )
        
        # Créer un identifiant unique pour le document
        document_id = str(uuid.uuid4())
        
        # Déterminer l'extension du fichier
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Créer le chemin de sauvegarde
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{document_id}{file_extension}")
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Créer le document dans la base de données
        document = await document_service.create_document(
            document_id=document_id,
            filename=filename,
            content_type=file.content_type,
            size=file_size,
            file_path=file_path
        )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            created_at=document.created_at,
            status=document.status,
            size=document.size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du téléchargement du document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="ID du document à récupérer"),
    document_service: DocumentService = Depends()
):
    """
    Récupère les informations d'un document
    """
    try:
        document = await document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document avec l'ID {document_id} non trouvé"
            )
            
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            created_at=document.created_at,
            status=document.status,
            size=document.size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du document: {str(e)}"
        )


@router.put("/{document_id}/type", response_model=DocumentResponse)
async def update_document_type(
    document_id: str = Path(..., description="ID du document à mettre à jour"),
    document_type: DocumentType = Query(..., description="Type de document"),
    document_service: DocumentService = Depends()
):
    """
    Met à jour le type d'un document
    """
    try:
        document = await document_service.update_document_type(document_id, document_type)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document avec l'ID {document_id} non trouvé"
            )
            
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            created_at=document.created_at,
            status=document.status,
            size=document.size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour du type de document: {str(e)}"
        )


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: str = Path(..., description="ID du document à supprimer"),
    document_service: DocumentService = Depends()
):
    """
    Supprime un document
    """
    try:
        success = await document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Document avec l'ID {document_id} non trouvé"
            )
            
        return {"message": f"Document avec l'ID {document_id} supprimé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, description="Nombre maximum d'éléments à retourner"),
    document_service: DocumentService = Depends()
):
    """
    Liste tous les documents
    """
    try:
        documents = await document_service.list_documents(skip, limit)
        
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                document_type=doc.document_type,
                created_at=doc.created_at,
                status=doc.status,
                size=doc.size
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des documents: {str(e)}"
        )

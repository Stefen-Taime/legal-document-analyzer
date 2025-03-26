from fastapi import APIRouter, HTTPException, Depends, Body, Form, UploadFile, File, Path, Query, BackgroundTasks
from typing import List, Optional, Dict
from datetime import datetime
import os
import uuid
import logging

from app.models.analysis import AnalysisCreate, AnalysisResponse, Clause, Risk, Recommendation, AnalysisStatus
from app.services.analysis_service import AnalysisService
from app.services.document_service import DocumentService
from app.services.vector_service import VectorService
from app.workflows.orchestrator import Orchestrator

# Configuration du logger
logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter()

# Service dependencies
def get_analysis_service():
    return AnalysisService()

def get_document_service():
    return DocumentService()

def get_vector_service():
    return VectorService()

def get_orchestrator():
    return Orchestrator()

# ===== ROUTES AVEC CHEMINS FIXES (sans paramètres de chemin) =====
# Ces routes doivent être définies AVANT les routes avec paramètres dynamiques

@router.post("/document", response_model=AnalysisResponse)
async def analyze_document(
    document_id: str = Form(...),
    document_type: Optional[str] = Form(None),
    file: Optional[UploadFile] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service),
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Analyse un document juridique
    
    Cette route permet de démarrer l'analyse d'un document juridique.
    L'analyse se fait en arrière-plan et le statut peut être vérifié via l'endpoint /status.
    """
    logger.info(f"Début d'analyse pour document_id={document_id}, type={document_type}")
    
    # Gérer le cas d'un fichier local
    if document_id == "local_file" and file:
        # Télécharger d'abord le fichier
        try:
            logger.info(f"Téléchargement d'un fichier local: {file.filename}")
            
            # Lire le contenu du fichier
            content = await file.read()
            file_size = len(content)
            
            # Revenir au début du fichier
            await file.seek(0)
            
            # Créer un document temporaire
            temp_document_id = str(uuid.uuid4())
            filename = file.filename
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Créer le chemin de sauvegarde
            upload_dir = "/app/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{temp_document_id}{file_extension}")
            
            # Sauvegarder le fichier
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Fichier sauvegardé: {file_path}")
            
            # Créer le document dans la base de données
            document = await document_service.create_document(
                document_id=temp_document_id,
                filename=filename,
                content_type=file.content_type,
                size=file_size,
                file_path=file_path,
                document_type=document_type  # Utiliser le type de document fourni
            )
            
            # Remplacer l'ID local par l'ID réel
            document_id = temp_document_id
            logger.info(f"Document créé avec ID: {document_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document local: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du téléchargement du document local: {str(e)}"
            )
    # Si on utilise "local_file" sans fournir de fichier, c'est une erreur
    elif document_id == "local_file":
        logger.error("Tentative d'analyse d'un document local sans fichier fourni")
        raise HTTPException(
            status_code=400, 
            detail="Document non téléchargé. Veuillez d'abord télécharger le document."
        )
    
    # Vérifier si le document existe dans la base de données
    document = await document_service.get_document(document_id)
    if not document:
        logger.error(f"Document avec ID {document_id} non trouvé")
        raise HTTPException(status_code=404, detail=f"Document avec ID {document_id} non trouvé")
    
    logger.info(f"Document trouvé: {document.filename}, type={document.document_type}")
    
    # Si un type de document est spécifié, mettre à jour le document
    if document_type and document.document_type != document_type:
        logger.info(f"Mise à jour du type de document: {document_type}")
        document = await document_service.update_document_type(
            document_id=document_id,
            document_type=document_type
        )
    
    # Créer une entrée d'analyse avec le statut "pending"
    try:
        logger.info(f"Création d'une nouvelle analyse pour document_id={document_id}")
        analysis = await analysis_service.create_analysis(
            document_id=document_id,
            document_type=document.document_type or document_type
        )
        
        # Lancer l'analyse en tâche de fond
        logger.info(f"Démarrage de l'analyse en tâche de fond: analysis_id={analysis.id}")
        background_tasks.add_task(
            orchestrator.run_analysis_workflow,
            analysis_id=analysis.id,
            document_id=document_id,
            document_type=document.document_type or document_type
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'analyse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du démarrage de l'analyse: {str(e)}"
        )

@router.get("/history", response_model=List[AnalysisResponse])
async def get_analysis_history(
    limit: int = Query(10, description="Nombre maximum d'éléments à retourner"),
    skip: int = Query(0, description="Nombre d'éléments à sauter"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Récupère l'historique des analyses
    
    Cette route permet de récupérer l'historique des analyses effectuées,
    triées par date de création (la plus récente en premier).
    """
    logger.info(f"Récupération de l'historique des analyses: skip={skip}, limit={limit}")
    try:
        analyses = await analysis_service.list_analyses(skip, limit)
        logger.info(f"Nombre d'analyses récupérées: {len(analyses)}")
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )

@router.post("/search", response_model=List[AnalysisResponse])
async def search_analysis(
    query: str = Body(..., embed=True),
    limit: int = Query(10, description="Nombre maximum d'éléments à retourner"),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Recherche des analyses similaires en utilisant la base vectorielle
    
    Cette route permet de rechercher des précédents juridiques similaires
    à la requête fournie, en utilisant la recherche vectorielle.
    """
    logger.info(f"Recherche d'analyses similaires: query={query[:50]}..., limit={limit}")
    try:
        # Rechercher des précédents similaires
        precedents = await vector_service.search_precedents(query, limit)
        logger.info(f"Nombre de précédents trouvés: {len(precedents)}")
        
        # Convertir les précédents en format d'analyse pour la réponse
        analyses = []
        for precedent in precedents:
            # Créer une analyse factice basée sur le précédent
            analysis = AnalysisResponse(
                id=precedent.id if hasattr(precedent, 'id') else str(uuid.uuid4()),
                document_id="",  # Pas de document associé
                document_type=precedent.type,
                status="completed",
                created_at=datetime.now(),
                results={
                    "clauses": [],
                    "risks": [],
                    "recommendations": [],
                    "precedent": precedent.dict()
                },
                similarity_score=precedent.similarity_score
            )
            analyses.append(analysis)
        
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {str(e)}"
        )

# ===== ROUTES AVEC PARAMÈTRES DE CHEMIN =====
# Ces routes doivent être définies APRÈS les routes avec chemins fixes

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Récupère les résultats d'une analyse spécifique
    
    Cette route permet de récupérer les détails complets d'une analyse,
    y compris ses résultats si elle est terminée.
    """
    logger.info(f"Récupération de l'analyse: analysis_id={analysis_id}")
    analysis = await analysis_service.get_analysis(analysis_id)
    if not analysis:
        logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    logger.info(f"Analyse récupérée: status={analysis.status}")
    return analysis

@router.get("/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Récupère le statut d'une analyse en cours
    
    Cette route permet de vérifier l'état d'avancement d'une analyse.
    Elle retourne des informations différentes selon le statut de l'analyse.
    """
    logger.info(f"Vérification du statut: analysis_id={analysis_id}")
    analysis = await analysis_service.get_analysis(analysis_id)
    if not analysis:
        logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    status_info = {
        "id": analysis.id,
        "status": analysis.status,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at
    }
    
    # Ajouter des informations supplémentaires selon le statut
    if analysis.status == "completed" and analysis.results:
        status_info["results"] = analysis.results
    elif analysis.status == "failed" and analysis.error:
        status_info["error"] = analysis.error
    elif analysis.status == "in_progress" and analysis.metadata and "progress" in analysis.metadata:
        status_info["progress"] = analysis.metadata["progress"]
    
    logger.info(f"Statut récupéré: status={analysis.status}")
    return status_info

@router.post("/{analysis_id}/retry", response_model=AnalysisResponse)
async def retry_analysis(
    analysis_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service),
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Relance une analyse qui a échoué
    
    Cette route permet de relancer une analyse qui a échoué.
    L'analyse sera relancée en arrière-plan.
    """
    logger.info(f"Tentative de relance d'analyse: analysis_id={analysis_id}")
    
    # Vérifier si l'analyse existe
    analysis = await analysis_service.get_analysis(analysis_id)
    if not analysis:
        logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    # Vérifier si l'analyse peut être relancée (a échoué)
    if analysis.status != "failed":
        logger.error(f"Impossible de relancer l'analyse: status={analysis.status}")
        raise HTTPException(
            status_code=400, 
            detail="Seules les analyses ayant échoué peuvent être relancées"
        )
    
    # Récupérer le document associé
    document = await document_service.get_document(analysis.document_id)
    if not document:
        logger.error(f"Document associé non trouvé: document_id={analysis.document_id}")
        raise HTTPException(
            status_code=404, 
            detail="Document associé à l'analyse non trouvé"
        )
    
    # Relancer l'analyse
    try:
        # Mettre à jour le statut
        logger.info(f"Mise à jour du statut: analysis_id={analysis_id}, status=pending")
        await analysis_service.update_analysis_status(analysis_id, AnalysisStatus.PENDING)
        
        # Lancer l'analyse en tâche de fond
        logger.info(f"Redémarrage de l'analyse en tâche de fond: analysis_id={analysis_id}")
        background_tasks.add_task(
            orchestrator.run_analysis_workflow,
            analysis_id=analysis_id,
            document_id=document.id,
            document_type=document.document_type
        )
        
        # Récupérer l'analyse mise à jour
        updated_analysis = await analysis_service.get_analysis(analysis_id)
        return updated_analysis
        
    except Exception as e:
        logger.error(f"Erreur lors de la relance de l'analyse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la relance de l'analyse: {str(e)}"
        )

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Supprime une analyse
    
    Cette route permet de supprimer définitivement une analyse et ses résultats.
    """
    logger.info(f"Suppression d'analyse: analysis_id={analysis_id}")
    try:
        success = await analysis_service.delete_analysis(analysis_id)
        if not success:
            logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        logger.info(f"Analyse supprimée avec succès: analysis_id={analysis_id}")
        return {"status": "success", "message": "Analyse supprimée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'analyse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression de l'analyse: {str(e)}"
        )

@router.get("/{analysis_id}/results")
async def get_analysis_results(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Récupère uniquement les résultats d'une analyse
    
    Cette route permet de récupérer uniquement les résultats d'une analyse terminée,
    sans les autres informations de l'analyse.
    """
    logger.info(f"Récupération des résultats d'analyse: analysis_id={analysis_id}")
    analysis = await analysis_service.get_analysis(analysis_id)
    
    if not analysis:
        logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    if analysis.status != "completed":
        logger.error(f"Analyse non terminée: analysis_id={analysis_id}, status={analysis.status}")
        raise HTTPException(status_code=400, detail="L'analyse n'est pas encore terminée")
    
    if not analysis.results:
        logger.error(f"Résultats d'analyse non disponibles: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Résultats d'analyse non disponibles")
    
    logger.info(f"Résultats d'analyse récupérés: analysis_id={analysis_id}")
    return analysis.results

@router.get("/{analysis_id}/document")
async def get_analysis_document(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Récupère le document associé à une analyse
    
    Cette route permet de récupérer les informations du document
    qui a été analysé dans une analyse spécifique.
    """
    logger.info(f"Récupération du document d'une analyse: analysis_id={analysis_id}")
    analysis = await analysis_service.get_analysis(analysis_id)
    
    if not analysis:
        logger.error(f"Analyse non trouvée: analysis_id={analysis_id}")
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    document = await document_service.get_document(analysis.document_id)
    
    if not document:
        logger.error(f"Document associé non trouvé: document_id={analysis.document_id}")
        raise HTTPException(status_code=404, detail="Document associé non trouvé")
    
    logger.info(f"Document d'analyse récupéré: document_id={document.id}")
    return document
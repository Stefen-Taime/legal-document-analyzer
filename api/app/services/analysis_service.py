from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import uuid
import time
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from app.models.analysis import Analysis, AnalysisStatus, AnalysisResults
from app.models.document import Document, DocumentStatus

# Configuration du logger
logger = logging.getLogger(__name__)

class AnalysisService:
    """Service pour la gestion des analyses de documents juridiques"""
    
    def __init__(self):
        # Connexion à MongoDB
        # Récupérer les variables d'environnement pour MongoDB
        mongodb_user = os.getenv("MONGODB_USER", "admin")
        mongodb_password = os.getenv("MONGODB_PASSWORD", "password_securise")
        mongodb_host = os.getenv("MONGODB_HOST", "mongodb")
        mongodb_port = os.getenv("MONGODB_PORT", "27017")
        mongodb_db = os.getenv("MONGODB_DB", "legal_analyzer")

        # Construire l'URI avec authentification
        mongodb_uri = f"mongodb://{mongodb_user}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_db}?authSource=admin"
        
        try:
            # Connexion à MongoDB avec l'URI authentifié
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client.get_database()
            self.collection = self.db.analyses
            
            # Créer un index sur le champ "id" pour optimiser les recherches
            logger.info("Initialisation du service d'analyse avec la connexion à MongoDB")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à MongoDB: {str(e)}", exc_info=True)
            raise
        
    async def create_analysis(
        self,
        document_id: str,
        document_type: str
    ) -> Analysis:
        """Crée une nouvelle analyse dans la base de données"""
        logger.info(f"Création d'une nouvelle analyse pour document_id={document_id}")
        
        analysis_id = str(uuid.uuid4())
        
        analysis = Analysis(
            id=analysis_id,
            document_id=document_id,
            document_type=document_type,
            status=AnalysisStatus.PENDING,
            metadata={
                "progress": 0.0,
                "started_at": datetime.now().isoformat()
            }
        )
        
        # Convertir le modèle Pydantic en dictionnaire
        analysis_dict = analysis.dict()
        
        try:
            # Insérer dans MongoDB
            await self.collection.insert_one(analysis_dict)
            logger.info(f"Analyse créée: analysis_id={analysis_id}")
            return analysis
        except DuplicateKeyError:
            logger.error(f"Une analyse avec l'ID {analysis_id} existe déjà")
            raise ValueError(f"Une analyse avec l'ID {analysis_id} existe déjà")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'analyse: {str(e)}", exc_info=True)
            raise
    
    async def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """Récupère une analyse par son ID"""
        try:
            analysis_dict = await self.collection.find_one({"id": analysis_id})
            
            if not analysis_dict:
                logger.info(f"Analyse non trouvée: analysis_id={analysis_id}")
                return None
                
            return Analysis(**analysis_dict)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'analyse: {str(e)}", exc_info=True)
            raise
    
    async def update_analysis_status(
        self,
        analysis_id: str,
        status: AnalysisStatus,
        error: Optional[str] = None
    ) -> Optional[Analysis]:
        """Met à jour le statut d'une analyse"""
        logger.info(f"Mise à jour du statut: analysis_id={analysis_id}, status={status}")
        
        try:
            # Vérifier que l'analyse existe
            analysis = await self.get_analysis(analysis_id)
            
            if not analysis:
                logger.warning(f"Tentative de mise à jour d'une analyse inexistante: analysis_id={analysis_id}")
                return None
                
            # Mettre à jour le statut, l'erreur et la date de mise à jour
            analysis.status = status
            analysis.error = error
            analysis.updated_at = datetime.now()
            
            # Si l'analyse est terminée, calculer le temps de traitement
            if status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                processing_time = (analysis.updated_at - analysis.created_at).total_seconds()
                analysis.processing_time = processing_time
                logger.info(f"Analyse terminée: analysis_id={analysis_id}, temps={processing_time}s, statut={status}")
                
                # Si l'analyse a échoué, enregistrer l'erreur
                if status == AnalysisStatus.FAILED and error:
                    logger.error(f"Échec de l'analyse: analysis_id={analysis_id}, erreur={error}")
            
            # Mettre à jour dans MongoDB
            update_data = {
                "status": status,
                "updated_at": analysis.updated_at
            }
            
            if error is not None:
                update_data["error"] = error
                
            if status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                update_data["processing_time"] = analysis.processing_time
            
            await self.collection.update_one(
                {"id": analysis_id},
                {"$set": update_data}
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}", exc_info=True)
            raise
    
    async def update_analysis_progress(
        self,
        analysis_id: str,
        progress: float
    ) -> Optional[Analysis]:
        """Met à jour la progression d'une analyse"""
        logger.debug(f"Mise à jour de la progression: analysis_id={analysis_id}, progress={progress:.1f}")
        
        try:
            # Vérifier que l'analyse existe
            analysis = await self.get_analysis(analysis_id)
            
            if not analysis:
                logger.warning(f"Tentative de mise à jour d'une analyse inexistante: analysis_id={analysis_id}")
                return None
                
            # Mettre à jour la progression et la date de mise à jour
            if not analysis.metadata:
                analysis.metadata = {}
                
            analysis.metadata["progress"] = progress
            analysis.updated_at = datetime.now()
            
            # Mettre à jour dans MongoDB
            await self.collection.update_one(
                {"id": analysis_id},
                {"$set": {
                    "metadata.progress": progress,
                    "updated_at": analysis.updated_at
                }}
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la progression: {str(e)}", exc_info=True)
            raise
    
    async def update_analysis_results(
        self,
        analysis_id: str,
        results: AnalysisResults
    ) -> Optional[Analysis]:
        """Met à jour les résultats d'une analyse"""
        logger.info(f"Mise à jour des résultats: analysis_id={analysis_id}")
        
        try:
            # Vérifier que l'analyse existe
            analysis = await self.get_analysis(analysis_id)
            
            if not analysis:
                logger.warning(f"Tentative de mise à jour d'une analyse inexistante: analysis_id={analysis_id}")
                return None
                
            # Mettre à jour les résultats et la date de mise à jour
            analysis.results = results
            analysis.updated_at = datetime.now()
            
            # Mettre à jour dans MongoDB
            await self.collection.update_one(
                {"id": analysis_id},
                {"$set": {
                    "results": results.dict(),
                    "updated_at": analysis.updated_at
                }}
            )
            
            logger.info(f"Résultats mis à jour: analysis_id={analysis_id}")
            return analysis
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des résultats: {str(e)}", exc_info=True)
            raise
    
    async def delete_analysis(self, analysis_id: str) -> bool:
        """Supprime une analyse"""
        logger.info(f"Suppression d'analyse: analysis_id={analysis_id}")
        
        try:
            # Vérifier que l'analyse existe
            analysis = await self.get_analysis(analysis_id)
            
            if not analysis:
                logger.warning(f"Tentative de suppression d'une analyse inexistante: analysis_id={analysis_id}")
                return False
                
            # Supprimer de MongoDB
            result = await self.collection.delete_one({"id": analysis_id})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Analyse supprimée: analysis_id={analysis_id}")
            else:
                logger.warning(f"Échec de la suppression: analysis_id={analysis_id}")
                
            return success
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'analyse: {str(e)}", exc_info=True)
            raise
    
    async def list_analyses(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """Liste toutes les analyses"""
        logger.info(f"Récupération de la liste des analyses: skip={skip}, limit={limit}")
        
        try:
            cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
            analyses = []
            
            async for analysis_dict in cursor:
                analyses.append(Analysis(**analysis_dict))
                
            logger.info(f"Analyses récupérées: count={len(analyses)}")
            return analyses
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des analyses: {str(e)}", exc_info=True)
            raise
        
    async def analyze_document(self, document: Document) -> Analysis:
        """Analyse un document et retourne les résultats
        
        Note: Cette méthode est désormais obsolète, utilisez plutôt l'orchestrateur
        qui effectue l'analyse en arrière-plan.
        """
        logger.warning("Utilisation de la méthode obsolète analyze_document. Utilisez plutôt l'orchestrateur.")
        
        # Créer une nouvelle analyse
        analysis = await self.create_analysis(
            document_id=document.id,
            document_type=document.document_type if document.document_type else "unknown"
        )
        
        # Mettre à jour le statut en cours
        await self.update_analysis_status(analysis.id, AnalysisStatus.IN_PROGRESS)
        
        try:
            # Créer des résultats d'analyse simples (pour l'exemple)
            from app.models.analysis import AnalysisResults, Clause, Risk, Recommendation, ClauseType, RiskLevel, Priority
            
            # Simuler un temps de traitement
            await self.update_analysis_progress(analysis.id, 0.5)
            logger.debug(f"Analyse en cours: analysis_id={analysis.id}, progress=50%")
            time.sleep(2)  # Simulation du temps de traitement
            await self.update_analysis_progress(analysis.id, 1.0)
            logger.debug(f"Analyse en cours: analysis_id={analysis.id}, progress=100%")
            
            # Version simplifiée - dans la production, vous implémenteriez votre logique d'analyse ici
            results = AnalysisResults(
                clauses=[
                    Clause(
                        title="Clause exemple",
                        content=f"Contenu extrait de {document.filename}",
                        type=ClauseType.CONFIDENTIALITY,
                        risk_level=RiskLevel.MEDIUM,
                        analysis="Analyse simple pour exemple"
                    )
                ],
                risks=[
                    Risk(
                        title="Risque exemple",
                        description="Description du risque pour exemple",
                        level=RiskLevel.MEDIUM,
                        impact="Impact potentiel pour exemple"
                    )
                ],
                recommendations=[
                    Recommendation(
                        title="Recommandation exemple",
                        description="Description de la recommandation pour exemple",
                        priority=Priority.MEDIUM
                    )
                ],
                summary="Résumé de l'analyse pour exemple"
            )
            
            # Mettre à jour les résultats
            await self.update_analysis_results(analysis.id, results)
            
            # Mettre à jour le statut terminé
            await self.update_analysis_status(analysis.id, AnalysisStatus.COMPLETED)
            
            # Récupérer l'analyse complète
            return await self.get_analysis(analysis.id)
            
        except Exception as e:
            # En cas d'erreur, mettre à jour le statut
            logger.error(f"Erreur lors de l'analyse du document: {str(e)}", exc_info=True)
            await self.update_analysis_status(
                analysis.id, 
                AnalysisStatus.FAILED, 
                str(e)
            )
            raise
            
    async def get_history(self, limit: int = 10) -> List[Analysis]:
        """Récupère l'historique des analyses"""
        return await self.list_analyses(limit=limit)
        
    async def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Obtient le statut actuel d'une analyse"""
        analysis = await self.get_analysis(analysis_id)
        
        if not analysis:
            return None
            
        status_info = {
            "id": analysis.id,
            "status": analysis.status,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at
        }
        
        # Ajouter des informations supplémentaires selon le statut
        if analysis.status == AnalysisStatus.COMPLETED and analysis.results:
            status_info["results"] = analysis.results
        elif analysis.status == AnalysisStatus.FAILED and analysis.error:
            status_info["error"] = analysis.error
        elif analysis.status == AnalysisStatus.IN_PROGRESS:
            if analysis.metadata and "progress" in analysis.metadata:
                status_info["progress"] = analysis.metadata["progress"]
            else:
                status_info["progress"] = 0.0
        
        return status_info
        
    async def retry_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """Relance une analyse échouée"""
        logger.info(f"Tentative de relance d'analyse: analysis_id={analysis_id}")
        
        try:
            analysis = await self.get_analysis(analysis_id)
            
            if not analysis:
                logger.warning(f"Tentative de relance d'une analyse inexistante: analysis_id={analysis_id}")
                return None
                
            if analysis.status != AnalysisStatus.FAILED:
                logger.warning(f"Tentative de relance d'une analyse non échouée: analysis_id={analysis_id}, status={analysis.status}")
                return None
                
            # Mettre à jour le statut à 'en attente'
            await self.update_analysis_status(analysis_id, AnalysisStatus.PENDING)
            logger.info(f"Analyse remise en attente pour relance: analysis_id={analysis_id}")
            
            # Retourner l'analyse mise à jour
            return await self.get_analysis(analysis_id)
        except Exception as e:
            logger.error(f"Erreur lors de la relance de l'analyse: {str(e)}", exc_info=True)
            raise
            
    async def process_analysis(self, analysis_id: str, document_id: str):
        """
        Traite une analyse en arrière-plan
        
        Cette méthode est utilisée comme point d'entrée pour le traitement
        en arrière-plan des analyses, via l'orchestrateur.
        """
        logger.info(f"Démarrage du traitement en arrière-plan: analysis_id={analysis_id}")
        
        try:
            # Mettre à jour le statut
            await self.update_analysis_status(analysis_id, AnalysisStatus.IN_PROGRESS)
            
            # Récupérer le document
            from app.services.document_service import DocumentService
            document_service = DocumentService()
            document = await document_service.get_document(document_id)
            
            if not document:
                logger.error(f"Document non trouvé: document_id={document_id}")
                await self.update_analysis_status(
                    analysis_id, 
                    AnalysisStatus.FAILED,
                    "Document non trouvé"
                )
                return
            
            # Lancer l'analyse complète via l'orchestrateur
            from app.workflows.orchestrator import Orchestrator
            orchestrator = Orchestrator()
            await orchestrator.run_analysis_workflow(
                analysis_id=analysis_id,
                document_id=document_id,
                document_type=document.document_type
            )
            
        except Exception as e:
            # En cas d'erreur, mettre à jour le statut
            logger.error(f"Erreur lors du traitement en arrière-plan: {str(e)}", exc_info=True)
            await self.update_analysis_status(
                analysis_id,
                AnalysisStatus.FAILED,
                str(e)
            )
            
    async def test_mongodb_connection(self) -> bool:
        """
        Teste la connexion à MongoDB
        
        Cette méthode peut être utilisée pour vérifier que la connexion
        à la base de données fonctionne correctement.
        """
        try:
            # Tenter de récupérer la liste des collections
            collections = await self.db.list_collection_names()
            logger.info(f"Connexion à MongoDB réussie. Collections: {', '.join(collections)}")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion à MongoDB: {str(e)}", exc_info=True)
            return False
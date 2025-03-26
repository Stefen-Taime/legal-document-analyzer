from typing import Dict, Any, Optional, List, Tuple
import os
import json
import time
import asyncio
import traceback
from datetime import datetime
import redis
from motor.motor_asyncio import AsyncIOMotorClient
import pypdf
import docx2txt
import logging

from app.models.document import DocumentType, DocumentStatus
from app.models.analysis import AnalysisStatus, AnalysisResults, Clause, Recommendation, Risk, Precedent, ClauseType, RiskLevel, Priority
from app.services.document_service import DocumentService
from app.services.analysis_service import AnalysisService
from app.services.vector_service import VectorService
from app.llm.llm_factory import LLMService, LLMProvider

# Configuration du logger
logger = logging.getLogger(__name__)

class Orchestrator:
    """Orchestrateur pour les workflows d'analyse de documents juridiques"""
    
    def __init__(
        self,
        document_service: Optional[DocumentService] = None,
        analysis_service: Optional[AnalysisService] = None,
        vector_service: Optional[VectorService] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.document_service = document_service or DocumentService()
        self.analysis_service = analysis_service or AnalysisService()
        self.vector_service = vector_service or VectorService()
        self.llm_service = llm_service or LLMService()
        
        # Connexion à Redis pour le stockage du contexte
        redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
        self.redis = redis.from_url(redis_uri)
        
        try:
            # Tester la connexion Redis
            self.redis.ping()
            logger.info("Connexion à Redis établie avec succès")
        except Exception as e:
            logger.error(f"Erreur de connexion à Redis: {str(e)}")
        
    def normalize_clause_type(self, type_str: str) -> str:
        """Normalise le type de clause pour qu'il corresponde à l'énumération ClauseType"""
        # Conversion en minuscules et retirer les accents
        normalized = type_str.lower().strip()
        
        # Mapping des types courants vers les valeurs de l'énumération
        type_mapping = {
            'confidentialité': 'confidentiality',
            'obligation de confidentialité': 'confidentiality',
            'clause de confidentialité': 'confidentiality',
            'confidentialite': 'confidentiality',
            'obligation': 'obligation',
            'restrictions': 'restriction',
            'restriction': 'restriction',
            'droit': 'right',
            'droits': 'right',
            'résiliation': 'termination',
            'resiliation': 'termination',
            'propriété intellectuelle': 'intellectual_property',
            'propriete intellectuelle': 'intellectual_property',
            'responsabilité': 'liability',
            'responsabilite': 'liability',
            'paiement': 'payment',
            'durée': 'duration',
            'duree': 'duration',
            'autre': 'other',
        }
        
        # Recherche par sous-chaîne pour les cas où le type contient les mots-clés
        for key, value in type_mapping.items():
            if key in normalized:
                return value
        
        # Retourner le type normalisé ou 'other' par défaut
        return 'other'
    
    def normalize_priority(self, priority_value: Any) -> int:
        """Normalise la priorité pour qu'elle corresponde à l'énumération Priority"""
        if isinstance(priority_value, int) and 1 <= priority_value <= 3:
            return priority_value
        
        if isinstance(priority_value, str):
            priority_str = priority_value.lower().strip()
            priority_mapping = {
                'faible': 1,
                'basse': 1,
                'low': 1,
                'moyenne': 2,
                'medium': 2,
                'élevée': 3,
                'elevee': 3,
                'haute': 3,
                'high': 3,
                '1': 1,
                '2': 2,
                '3': 3,
            }
            for key, value in priority_mapping.items():
                if key in priority_str:
                    return value
        
        # Valeur par défaut
        return 2  # Medium/Moyenne par défaut
    
    def normalize_risk_level(self, level_value: Any) -> int:
        """Normalise le niveau de risque pour qu'il corresponde à l'énumération RiskLevel"""
        if isinstance(level_value, int) and 1 <= level_value <= 5:
            return level_value
        
        if isinstance(level_value, str):
            try:
                level_int = int(level_value)
                if 1 <= level_int <= 5:
                    return level_int
            except ValueError:
                # Si la conversion échoue, on continue avec la recherche par mot-clé
                pass
            
            level_str = level_value.lower().strip()
            level_mapping = {
                'très faible': 1,
                'tres faible': 1,
                'faible': 2,
                'moyen': 3,
                'élevé': 4,
                'eleve': 4,
                'très élevé': 5,
                'tres eleve': 5,
                'very low': 1,
                'low': 2,
                'medium': 3,
                'high': 4,
                'very high': 5
            }
            for key, value in level_mapping.items():
                if key in level_str:
                    return value
        
        # Valeur par défaut
        return 3  # Medium/Moyen par défaut
        
    async def extract_text_from_document(self, document_id: str) -> Optional[str]:
        """Extrait le texte d'un document"""
        
        document = await self.document_service.get_document(document_id)
        
        if not document:
            logger.error(f"Document non trouvé: {document_id}")
            return None
            
        file_path = document.file_path
        
        if not os.path.exists(file_path):
            logger.error(f"Fichier non trouvé: {file_path}")
            return None
            
        text_content = ""
        
        try:
            # Extraire le texte selon le type de fichier
            if file_path.lower().endswith(".pdf"):
                # Extraire le texte d'un PDF
                with open(file_path, "rb") as f:
                    pdf = pypdf.PdfReader(f)
                    for page in pdf.pages:
                        text_content += page.extract_text() + "\n\n"
                        
            elif file_path.lower().endswith((".docx", ".doc")):
                # Extraire le texte d'un document Word
                text_content = docx2txt.process(file_path)
                
            elif file_path.lower().endswith(".txt"):
                # Lire un fichier texte
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
                    
            else:
                logger.error(f"Format de fichier non supporté: {file_path}")
                return None
                
            # Mettre à jour le contenu texte du document
            await self.document_service.update_document_text_content(document_id, text_content)
            
            logger.info(f"Texte extrait avec succès: {len(text_content)} caractères")
            return text_content
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du texte: {str(e)}", exc_info=True)
            return None
    
    async def run_analysis_workflow(
        self,
        analysis_id: str,
        document_id: str,
        document_type: str
    ):
        """Exécute le workflow complet d'analyse d'un document"""
        
        try:
            logger.info(f"Démarrage de l'analyse: analysis_id={analysis_id}, document_id={document_id}")
            
            # Mettre à jour le statut de l'analyse
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.IN_PROGRESS
            )
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.1
            )
            
            # Extraire le texte du document
            document_text = await self.extract_text_from_document(document_id)
            
            if not document_text:
                logger.error(f"Impossible d'extraire le texte du document: {document_id}")
                await self.analysis_service.update_analysis_status(
                    analysis_id=analysis_id,
                    status=AnalysisStatus.FAILED,
                    error="Impossible d'extraire le texte du document"
                )
                return
                
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.2
            )
            
            # Extraire les clauses du document
            logger.info("Extraction des clauses...")
            clauses_data = await self.llm_service.extract_clauses(
                document_text=document_text,
                document_type=document_type
            )
            
            # Convertir les données en modèles Clause
            clauses = []
            for clause_data in clauses_data:
                try:
                    # Normaliser le type de clause
                    normalized_type = self.normalize_clause_type(clause_data["type"])
                    
                    # Normaliser le niveau de risque
                    normalized_risk = self.normalize_risk_level(clause_data["risk_level"])
                    
                    clause = Clause(
                        title=clause_data["title"],
                        content=clause_data["content"],
                        type=normalized_type,
                        risk_level=normalized_risk,
                        analysis=clause_data["analysis"]
                    )
                    clauses.append(clause)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'une clause: {str(e)}")
                    logger.debug(f"Données de la clause problématique: {clause_data}")
            
            # Ajouter une clause par défaut si aucune clause n'a été extraite
            if not clauses:
                logger.warning("Aucune clause n'a été extraite, ajout d'une clause par défaut")
                default_clause = Clause(
                    title="Document incomplet",
                    content="Le document ne contient pas de clauses explicites ou les clauses n'ont pas pu être correctement extraites.",
                    type=ClauseType.OTHER,
                    risk_level=RiskLevel.MEDIUM,
                    analysis="Ce document semble incomplet ou non structuré. Il est recommandé d'ajouter des clauses explicites pour couvrir les aspects importants du type de contrat concerné."
                )
                clauses.append(default_clause)
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.4
            )
            
            # Générer des recommandations
            logger.info("Génération des recommandations...")
            recommendations_data = await self.llm_service.generate_recommendations(
                clauses=clauses_data,
                document_type=document_type
            )
            
            # Convertir les données en modèles Recommendation
            recommendations = []
            for recommendation_data in recommendations_data:
                try:
                    # Normaliser la priorité
                    normalized_priority = self.normalize_priority(recommendation_data["priority"])
                    
                    recommendation = Recommendation(
                        title=recommendation_data["title"],
                        description=recommendation_data["description"],
                        priority=normalized_priority,
                        suggested_text=recommendation_data.get("suggested_text"),
                        related_clauses=recommendation_data.get("related_clauses", [])
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'une recommandation: {str(e)}")
                    logger.debug(f"Données de la recommandation problématique: {recommendation_data}")
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.6
            )
            
            # Identifier les risques
            logger.info("Identification des risques...")
            risks_data = await self.llm_service.identify_risks(
                clauses=clauses_data,
                document_type=document_type
            )
            
            # Convertir les données en modèles Risk
            risks = []
            for risk_data in risks_data:
                try:
                    # Normaliser le niveau de risque
                    normalized_level = self.normalize_risk_level(risk_data["level"])
                    
                    risk = Risk(
                        title=risk_data["title"],
                        description=risk_data["description"],
                        level=normalized_level,
                        impact=risk_data["impact"],
                        mitigation=risk_data.get("mitigation")
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'un risque: {str(e)}")
                    logger.debug(f"Données du risque problématique: {risk_data}")
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.8
            )
            
            # Rechercher des précédents juridiques similaires
            logger.info("Recherche de précédents juridiques...")
            precedents = []
            
            # Utiliser les clauses à haut risque pour la recherche
            high_risk_clauses = [c for c in clauses if c.risk_level >= 4]
            
            if high_risk_clauses:
                logger.info(f"Recherche basée sur {len(high_risk_clauses)} clauses à haut risque")
                for clause in high_risk_clauses[:3]:  # Limiter à 3 clauses pour éviter trop de requêtes
                    clause_precedents = await self.vector_service.search_precedents(
                        query=clause.content,
                        limit=2
                    )
                    precedents.extend(clause_precedents)
            
            # Générer un résumé
            logger.info("Génération du résumé...")
            summary = await self.llm_service.generate_summary(
                document_text=document_text,
                clauses=clauses_data,
                risks=risks_data,
                document_type=document_type
            )
            
            # Créer les résultats de l'analyse
            results = AnalysisResults(
                clauses=clauses,
                recommendations=recommendations,
                risks=risks,
                precedents=precedents,
                summary=summary,
                metadata={
                    "document_type": document_type,
                    "analysis_date": datetime.now().isoformat()
                }
            )
            
            # Mettre à jour les résultats de l'analyse
            logger.info("Sauvegarde des résultats...")
            await self.analysis_service.update_analysis_results(
                analysis_id=analysis_id,
                results=results
            )
            
            # Mettre à jour le statut de l'analyse
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.COMPLETED
            )
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=1.0
            )
            
            # Mettre à jour le statut du document
            await self.document_service.update_document_status(
                document_id=document_id,
                status=DocumentStatus.PROCESSED
            )
            
            logger.info(f"Analyse terminée avec succès: analysis_id={analysis_id}")
            
        except Exception as e:
            # En cas d'erreur, mettre à jour le statut de l'analyse
            error_message = f"Erreur lors de l'analyse: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.FAILED,
                error=error_message
            )
            
    async def parallel_analysis_workflow(
        self,
        analysis_id: str,
        document_id: str,
        document_type: str
    ):
        """Exécute le workflow d'analyse en parallélisant certaines tâches"""
        
        try:
            logger.info(f"Démarrage de l'analyse parallèle: analysis_id={analysis_id}, document_id={document_id}")
            
            # Mettre à jour le statut de l'analyse
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.IN_PROGRESS
            )
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.1
            )
            
            # Extraire le texte du document
            document_text = await self.extract_text_from_document(document_id)
            
            if not document_text:
                logger.error(f"Impossible d'extraire le texte du document: {document_id}")
                await self.analysis_service.update_analysis_status(
                    analysis_id=analysis_id,
                    status=AnalysisStatus.FAILED,
                    error="Impossible d'extraire le texte du document"
                )
                return
                
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.2
            )
            
            # Extraire les clauses du document
            logger.info("Extraction des clauses (parallèle)...")
            clauses_task = asyncio.create_task(
                self.llm_service.extract_clauses(
                    document_text=document_text,
                    document_type=document_type
                )
            )
            
            # Attendre les résultats de l'extraction des clauses
            clauses_data = await clauses_task
            
            # Convertir les données en modèles Clause
            clauses = []
            for clause_data in clauses_data:
                try:
                    # Normaliser le type de clause
                    normalized_type = self.normalize_clause_type(clause_data["type"])
                    
                    # Normaliser le niveau de risque
                    normalized_risk = self.normalize_risk_level(clause_data["risk_level"])
                    
                    clause = Clause(
                        title=clause_data["title"],
                        content=clause_data["content"],
                        type=normalized_type,
                        risk_level=normalized_risk,
                        analysis=clause_data["analysis"]
                    )
                    clauses.append(clause)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'une clause: {str(e)}")
                    logger.debug(f"Données de la clause problématique: {clause_data}")
            
            # Ajouter une clause par défaut si aucune clause n'a été extraite
            if not clauses:
                logger.warning("Aucune clause n'a été extraite, ajout d'une clause par défaut")
                default_clause = Clause(
                    title="Document incomplet",
                    content="Le document ne contient pas de clauses explicites ou les clauses n'ont pas pu être correctement extraites.",
                    type=ClauseType.OTHER,
                    risk_level=RiskLevel.MEDIUM,
                    analysis="Ce document semble incomplet ou non structuré. Il est recommandé d'ajouter des clauses explicites pour couvrir les aspects importants du type de contrat concerné."
                )
                clauses.append(default_clause)
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.4
            )
            
            # Exécuter en parallèle la génération de recommandations et l'identification des risques
            logger.info("Génération des recommandations et identification des risques (parallèle)...")
            recommendations_task = asyncio.create_task(
                self.llm_service.generate_recommendations(
                    clauses=clauses_data,
                    document_type=document_type
                )
            )
            
            risks_task = asyncio.create_task(
                self.llm_service.identify_risks(
                    clauses=clauses_data,
                    document_type=document_type
                )
            )
            
            # Attendre les résultats des tâches parallèles
            recommendations_data, risks_data = await asyncio.gather(
                recommendations_task,
                risks_task
            )
            
            # Convertir les données en modèles
            recommendations = []
            for recommendation_data in recommendations_data:
                try:
                    # Normaliser la priorité
                    normalized_priority = self.normalize_priority(recommendation_data["priority"])
                    
                    recommendation = Recommendation(
                        title=recommendation_data["title"],
                        description=recommendation_data["description"],
                        priority=normalized_priority,
                        suggested_text=recommendation_data.get("suggested_text"),
                        related_clauses=recommendation_data.get("related_clauses", [])
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'une recommandation: {str(e)}")
                    logger.debug(f"Données de la recommandation problématique: {recommendation_data}")
            
            risks = []
            for risk_data in risks_data:
                try:
                    # Normaliser le niveau de risque
                    normalized_level = self.normalize_risk_level(risk_data["level"])
                    
                    risk = Risk(
                        title=risk_data["title"],
                        description=risk_data["description"],
                        level=normalized_level,
                        impact=risk_data["impact"],
                        mitigation=risk_data.get("mitigation")
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion d'un risque: {str(e)}")
                    logger.debug(f"Données du risque problématique: {risk_data}")
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.7
            )
            
            # Rechercher des précédents juridiques similaires et générer un résumé en parallèle
            logger.info("Recherche de précédents et génération du résumé (parallèle)...")
            precedents_tasks = []
            
            # Utiliser les clauses à haut risque pour la recherche
            high_risk_clauses = [c for c in clauses if c.risk_level >= 4]
            
            if high_risk_clauses:
                logger.info(f"Recherche basée sur {len(high_risk_clauses)} clauses à haut risque")
                for clause in high_risk_clauses[:3]:  # Limiter à 3 clauses pour éviter trop de requêtes
                    task = asyncio.create_task(
                        self.vector_service.search_precedents(
                            query=clause.content,
                            limit=2
                        )
                    )
                    precedents_tasks.append(task)
            
            summary_task = asyncio.create_task(
                self.llm_service.generate_summary(
                    document_text=document_text,
                    clauses=clauses_data,
                    risks=risks_data,
                    document_type=document_type
                )
            )
            
            # Attendre les résultats des tâches parallèles
            all_tasks = precedents_tasks + [summary_task]
            results = await asyncio.gather(*all_tasks)
            
            # Extraire les résultats
            precedents = []
            for i in range(len(precedents_tasks)):
                precedents.extend(results[i])
            
            summary = results[-1]  # Le dernier résultat est le résumé
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=0.9
            )
            
            # Créer les résultats de l'analyse
            analysis_results = AnalysisResults(
                clauses=clauses,
                recommendations=recommendations,
                risks=risks,
                precedents=precedents,
                summary=summary,
                metadata={
                    "document_type": document_type,
                    "analysis_date": datetime.now().isoformat()
                }
            )
            
            # Mettre à jour les résultats de l'analyse
            logger.info("Sauvegarde des résultats...")
            await self.analysis_service.update_analysis_results(
                analysis_id=analysis_id,
                results=analysis_results
            )
            
            # Mettre à jour le statut de l'analyse
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.COMPLETED
            )
            
            # Mettre à jour la progression
            await self.analysis_service.update_analysis_progress(
                analysis_id=analysis_id,
                progress=1.0
            )
            
            # Mettre à jour le statut du document
            await self.document_service.update_document_status(
                document_id=document_id,
                status=DocumentStatus.PROCESSED
            )
            
            logger.info(f"Analyse parallèle terminée avec succès: analysis_id={analysis_id}")
            
        except Exception as e:
            # En cas d'erreur, mettre à jour le statut de l'analyse
            error_message = f"Erreur lors de l'analyse parallèle: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            await self.analysis_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.FAILED,
                error=error_message
            )
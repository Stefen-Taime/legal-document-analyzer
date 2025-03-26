from typing import Dict, Any, Optional, List, Tuple
import os
import json
import time
import asyncio
import traceback
from datetime import datetime
import logging
import pypdf
import docx2txt

import redis
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from app.models.document import DocumentType, DocumentStatus
from app.models.analysis import (
    AnalysisStatus, AnalysisResults, Clause, Recommendation,
    Risk, Precedent, ClauseType, RiskLevel, Priority
)
from app.services.document_service import DocumentService
from app.services.analysis_service import AnalysisService
from app.services.vector_service import VectorService
from app.llm.llm_factory import LLMService, LLMProvider

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
        
        # -- Connexion à Redis (Option 2: on lit l'URI et le password séparément) --
        redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
        redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # On parse l'URI pour extraire host, port et db
        parsed_uri = urlparse(redis_uri)
        host = parsed_uri.hostname or "redis"
        port = parsed_uri.port or 6379
        
        db = 0
        if parsed_uri.path:
            db_str = parsed_uri.path.lstrip("/")
            if db_str.isdigit():
                db = int(db_str)
        
        # Construction de l'instance Redis
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=redis_password
        )
        
        try:
            # Tester la connexion Redis
            self.redis.ping()
            logger.info(f"Connexion à Redis établie avec succès sur {host}:{port}, db={db}")
        except Exception as e:
            logger.error(f"Erreur de connexion à Redis: {str(e)}")
        
    def normalize_clause_type(self, type_str: str) -> str:
        """Normalise le type de clause pour qu'il corresponde à l'énumération ClauseType."""
        normalized = type_str.lower().strip()
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
        
        for key, value in type_mapping.items():
            if key in normalized:
                return value
        
        return 'other'
    
    def normalize_priority(self, priority_value: Any) -> int:
        """Normalise la priorité pour qu'elle corresponde à l'énumération Priority."""
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
        
        return 2  # Medium par défaut
    
    def normalize_risk_level(self, level_value: Any) -> int:
        """Normalise le niveau de risque pour qu'il corresponde à l'énumération RiskLevel."""
        if isinstance(level_value, int) and 1 <= level_value <= 5:
            return level_value
        
        if isinstance(level_value, str):
            try:
                level_int = int(level_value)
                if 1 <= level_int <= 5:
                    return level_int
            except ValueError:
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
        
        return 3  # Moyen par défaut
    
    async def extract_text_from_document(self, document_id: str) -> Optional[str]:
        """Extrait le texte d'un document (PDF, Word, TXT)."""
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
            if file_path.lower().endswith(".pdf"):
                with open(file_path, "rb") as f:
                    pdf_reader = pypdf.PdfReader(f)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n\n"
            elif file_path.lower().endswith((".docx", ".doc")):
                text_content = docx2txt.process(file_path)
            elif file_path.lower().endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            else:
                logger.error(f"Format de fichier non supporté: {file_path}")
                return None
                
            await self.document_service.update_document_text_content(document_id, text_content)
            logger.info(f"Texte extrait avec succès: {len(text_content)} caractères.")
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
        """Exécute le workflow complet d'analyse d'un document."""
        try:
            logger.info(f"Démarrage de l'analyse: analysis_id={analysis_id}, document_id={document_id}")
            
            # 1) Mise à jour du statut (Mongo + Redis)
            await self.analysis_service.update_analysis_status(analysis_id, AnalysisStatus.IN_PROGRESS)
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.IN_PROGRESS.value)
            
            # 2) Progression (Mongo + Redis)
            await self.analysis_service.update_analysis_progress(analysis_id, 0.1)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.1)
            
            # 3) Extraire le texte
            document_text = await self.extract_text_from_document(document_id)
            if not document_text:
                logger.error(f"Impossible d'extraire le texte du document: {document_id}")
                await self.analysis_service.update_analysis_status(
                    analysis_id, AnalysisStatus.FAILED,
                    error="Impossible d'extraire le texte du document"
                )
                self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.FAILED.value)
                return
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.2)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.2)
            
            # 4) Extraction des clauses
            logger.info("Extraction des clauses...")
            clauses_data = await self.llm_service.extract_clauses(
                document_text=document_text,
                document_type=document_type
            )
            
            clauses = []
            for cdata in clauses_data:
                try:
                    ctype = self.normalize_clause_type(cdata["type"])
                    crisk = self.normalize_risk_level(cdata["risk_level"])
                    clause = Clause(
                        title=cdata["title"],
                        content=cdata["content"],
                        type=ctype,
                        risk_level=crisk,
                        analysis=cdata["analysis"]
                    )
                    clauses.append(clause)
                except Exception as e:
                    logger.error(f"Erreur clause: {str(e)}")
                    logger.debug(f"Clause data: {cdata}")
            
            if not clauses:
                logger.warning("Aucune clause n'a été extraite, ajout d'une clause par défaut.")
                default_clause = Clause(
                    title="Document incomplet",
                    content="Le document ne contient pas de clauses explicites ou elles n'ont pas pu être extraites.",
                    type=ClauseType.OTHER,
                    risk_level=RiskLevel.MEDIUM,
                    analysis="Document incomplet ou non structuré. Recommandé d'ajouter des clauses explicites."
                )
                clauses.append(default_clause)
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.4)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.4)
            
            # 5) Recommandations
            logger.info("Génération des recommandations...")
            recommendations_data = await self.llm_service.generate_recommendations(
                clauses=clauses_data,
                document_type=document_type
            )
            
            recommendations = []
            for rdata in recommendations_data:
                try:
                    rprio = self.normalize_priority(rdata["priority"])
                    rec = Recommendation(
                        title=rdata["title"],
                        description=rdata["description"],
                        priority=rprio,
                        suggested_text=rdata.get("suggested_text"),
                        related_clauses=rdata.get("related_clauses", [])
                    )
                    recommendations.append(rec)
                except Exception as e:
                    logger.error(f"Erreur recommandation: {str(e)}")
                    logger.debug(f"Reco data: {rdata}")
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.6)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.6)
            
            # 6) Identification des risques
            logger.info("Identification des risques...")
            risks_data = await self.llm_service.identify_risks(
                clauses=clauses_data,
                document_type=document_type
            )
            
            risks = []
            for rdata in risks_data:
                try:
                    level = self.normalize_risk_level(rdata["level"])
                    rk = Risk(
                        title=rdata["title"],
                        description=rdata["description"],
                        level=level,
                        impact=rdata["impact"],
                        mitigation=rdata.get("mitigation")
                    )
                    risks.append(rk)
                except Exception as e:
                    logger.error(f"Erreur risque: {str(e)}")
                    logger.debug(f"Risk data: {rdata}")
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.8)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.8)
            
            # 7) Recherche de précédents (deux approches combinées)
            logger.info("Recherche de précédents...")
            precedents = []
            
            # Approche 1: Recherche vectorielle pour les clauses à haut risque
            high_risk_clauses = [c for c in clauses if c.risk_level >= 4]
            if high_risk_clauses:
                logger.info(f"Recherche vectorielle basée sur {len(high_risk_clauses)} clauses à haut risque.")
                for c in high_risk_clauses[:3]:
                    clause_precedents = await self.vector_service.search_precedents(query=c.content, limit=2)
                    precedents.extend(clause_precedents)
            
            # Approche 2: Génération de précédents via LLM (si aucun précédent trouvé par vectorisation)
            if len(precedents) < 3:
                logger.info("Pas assez de précédents trouvés par vectorisation, utilisation du LLM.")
                try:
                    # Appeler identify_precedents
                    llm_precedents_data = await self.llm_service.identify_precedents(
                        clauses=clauses_data,
                        document_type=document_type
                    )
                    
                    # Convertir en objets Precedent
                    for p_data in llm_precedents_data:
                        precedent = Precedent(
                            title=p_data.get("title", ""),
                            description=p_data.get("description", ""),
                            type=p_data.get("type", ""),
                            relevance=p_data.get("relevance", ""),
                            source=p_data.get("source", ""),
                            similarity_score=0.95  # Score élevé pour les précédents générés par LLM
                        )
                        precedents.append(precedent)
                    
                    logger.info(f"Génération de précédents LLM réussie: {len(llm_precedents_data)} précédents.")
                except Exception as e:
                    logger.error(f"Erreur lors de la génération de précédents LLM: {str(e)}")
            
            # 8) Génération du résumé
            logger.info("Génération du résumé...")
            summary = await self.llm_service.generate_summary(
                document_text=document_text,
                clauses=clauses_data,
                risks=risks_data,
                document_type=document_type
            )
            
            # 9) Création des résultats finaux
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
            
            # 10) Sauvegarde (Mongo) + Update (Redis)
            logger.info("Sauvegarde des résultats...")
            await self.analysis_service.update_analysis_results(analysis_id, results)
            
            # Marquer l'analyse comme terminée
            await self.analysis_service.update_analysis_status(analysis_id, AnalysisStatus.COMPLETED)
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.COMPLETED.value)
            
            await self.analysis_service.update_analysis_progress(analysis_id, 1.0)
            self.redis.set(f"analysis:{analysis_id}:progress", 1.0)
            
            # Mettre à jour le document
            await self.document_service.update_document_status(document_id, DocumentStatus.PROCESSED)
            logger.info(f"Analyse terminée avec succès: analysis_id={analysis_id}")
            
        except Exception as e:
            error_message = f"Erreur lors de l'analyse: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            # Statut d'erreur
            await self.analysis_service.update_analysis_status(
                analysis_id, AnalysisStatus.FAILED,
                error=error_message
            )
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.FAILED.value)

    async def parallel_analysis_workflow(
        self,
        analysis_id: str,
        document_id: str,
        document_type: str
    ):
        """Exécute le workflow d'analyse en parallélisant certaines tâches."""
        try:
            logger.info(f"Démarrage de l'analyse parallèle: analysis_id={analysis_id}, document_id={document_id}")
            
            await self.analysis_service.update_analysis_status(analysis_id, AnalysisStatus.IN_PROGRESS)
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.IN_PROGRESS.value)
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.1)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.1)
            
            # Extraire le texte
            document_text = await self.extract_text_from_document(document_id)
            if not document_text:
                logger.error(f"Impossible d'extraire le texte du document: {document_id}")
                await self.analysis_service.update_analysis_status(
                    analysis_id, AnalysisStatus.FAILED,
                    error="Impossible d'extraire le texte du document"
                )
                self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.FAILED.value)
                return
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.2)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.2)
            
            # Extraction des clauses (parallèle)
            logger.info("Extraction des clauses (async)...")
            clauses_task = asyncio.create_task(
                self.llm_service.extract_clauses(document_text=document_text, document_type=document_type)
            )
            clauses_data = await clauses_task
            
            # Convertir en Clauses
            clauses = []
            for cdata in clauses_data:
                try:
                    ctype = self.normalize_clause_type(cdata["type"])
                    crisk = self.normalize_risk_level(cdata["risk_level"])
                    clause = Clause(
                        title=cdata["title"],
                        content=cdata["content"],
                        type=ctype,
                        risk_level=crisk,
                        analysis=cdata["analysis"]
                    )
                    clauses.append(clause)
                except Exception as e:
                    logger.error(f"Erreur clause: {str(e)}")
                    logger.debug(f"Clause data: {cdata}")
            
            if not clauses:
                logger.warning("Aucune clause extraite, ajout d'une clause par défaut.")
                default_clause = Clause(
                    title="Document incomplet",
                    content="Aucune clause explicite ou extraction impossible.",
                    type=ClauseType.OTHER,
                    risk_level=RiskLevel.MEDIUM,
                    analysis="Document incomplet, ajouter des clauses explicites."
                )
                clauses.append(default_clause)
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.4)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.4)
            
            # Recommandations + risques (parallèle)
            logger.info("Génération des recommandations + identification des risques...")
            recommendations_task = asyncio.create_task(
                self.llm_service.generate_recommendations(clauses=clauses_data, document_type=document_type)
            )
            risks_task = asyncio.create_task(
                self.llm_service.identify_risks(clauses=clauses_data, document_type=document_type)
            )
            recommendations_data, risks_data = await asyncio.gather(recommendations_task, risks_task)
            
            recommendations = []
            for rdata in recommendations_data:
                try:
                    rprio = self.normalize_priority(rdata["priority"])
                    rec = Recommendation(
                        title=rdata["title"],
                        description=rdata["description"],
                        priority=rprio,
                        suggested_text=rdata.get("suggested_text"),
                        related_clauses=rdata.get("related_clauses", [])
                    )
                    recommendations.append(rec)
                except Exception as e:
                    logger.error(f"Erreur recommendation: {str(e)}")
                    logger.debug(f"Reco data: {rdata}")
            
            risks = []
            for rdata in risks_data:
                try:
                    level = self.normalize_risk_level(rdata["level"])
                    rk = Risk(
                        title=rdata["title"],
                        description=rdata["description"],
                        level=level,
                        impact=rdata["impact"],
                        mitigation=rdata.get("mitigation")
                    )
                    risks.append(rk)
                except Exception as e:
                    logger.error(f"Erreur risque: {str(e)}")
                    logger.debug(f"Risk data: {rdata}")
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.7)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.7)
            
            # Recherche de précédents + résumé (parallèle)
            logger.info("Recherche de précédents + génération du résumé (async)...")
            
            # Tâches de recherche vectorielle
            precedents_tasks = []
            high_risk_clauses = [c for c in clauses if c.risk_level >= 4]
            if high_risk_clauses:
                logger.info(f"Recherche vectorielle via {len(high_risk_clauses)} clauses à haut risque.")
                for c in high_risk_clauses[:3]:
                    task = asyncio.create_task(
                        self.vector_service.search_precedents(query=c.content, limit=2)
                    )
                    precedents_tasks.append(task)
            
            # Tâche de génération LLM en parallèle
            llm_precedents_task = asyncio.create_task(
                self.llm_service.identify_precedents(
                    clauses=clauses_data,
                    document_type=document_type
                )
            )
            
            # Tâche du résumé
            summary_task = asyncio.create_task(
                self.llm_service.generate_summary(
                    document_text=document_text,
                    clauses=clauses_data,
                    risks=risks_data,
                    document_type=document_type
                )
            )
            
            # Attendre toutes les tâches
            vector_tasks_results = await asyncio.gather(*precedents_tasks, return_exceptions=True)
            
            # Traiter résultats vectoriels
            precedents = []
            for result in vector_tasks_results:
                if isinstance(result, list) and not isinstance(result, Exception):
                    precedents.extend(result)
            
            # Traiter les précédents LLM si nécessaire
            try:
                llm_precedents_data = await llm_precedents_task
                if len(precedents) < 3:
                    logger.info("Utilisation des précédents LLM pour compléter...")
                    for p_data in llm_precedents_data:
                        precedent = Precedent(
                            title=p_data.get("title", ""),
                            description=p_data.get("description", ""),
                            type=p_data.get("type", ""),
                            relevance=p_data.get("relevance", ""),
                            source=p_data.get("source", ""),
                            similarity_score=0.95
                        )
                        precedents.append(precedent)
            except Exception as e:
                logger.error(f"Erreur LLM précédents: {str(e)}")
            
            # Obtenir le résumé
            summary = await summary_task
            
            await self.analysis_service.update_analysis_progress(analysis_id, 0.9)
            self.redis.set(f"analysis:{analysis_id}:progress", 0.9)
            
            # Résultat final
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
            
            logger.info("Sauvegarde des résultats en base (Mongo)...")
            await self.analysis_service.update_analysis_results(analysis_id, analysis_results)
            
            await self.analysis_service.update_analysis_status(analysis_id, AnalysisStatus.COMPLETED)
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.COMPLETED.value)
            
            await self.analysis_service.update_analysis_progress(analysis_id, 1.0)
            self.redis.set(f"analysis:{analysis_id}:progress", 1.0)
            
            await self.document_service.update_document_status(document_id, DocumentStatus.PROCESSED)
            logger.info(f"Analyse parallèle terminée: analysis_id={analysis_id}")
        
        except Exception as e:
            error_message = f"Erreur lors de l'analyse parallèle: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            await self.analysis_service.update_analysis_status(analysis_id, AnalysisStatus.FAILED, error=error_message)
            self.redis.set(f"analysis:{analysis_id}:status", AnalysisStatus.FAILED.value)
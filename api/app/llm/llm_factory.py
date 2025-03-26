from typing import Dict, Any, Optional, List, Union
import os
import json
import time
import logging
from enum import Enum
import groq
import openai
import anthropic

# Configuration du logger
logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LLMFactory:
    """Fabrique pour créer des instances de LLM selon le fournisseur choisi"""
    
    def __init__(self):
        # Charger les clés API depuis les variables d'environnement
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Déterminer le fournisseur par défaut
        self.default_provider = os.getenv("LLM_PROVIDER", "groq")
        
        # Initialiser les clients
        self._init_clients()
        
    def _init_clients(self):
        """Initialise les clients pour chaque fournisseur"""
        self.clients = {}
        
        # Initialiser Groq si la clé est disponible
        if self.groq_api_key:
            try:
                self.clients[LLMProvider.GROQ] = groq.Groq(api_key=self.groq_api_key)
                logger.info("Client Groq initialisé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du client Groq: {str(e)}")
            
        # Initialiser OpenAI si la clé est disponible
        if self.openai_api_key:
            try:
                # Utiliser directement le module openai au lieu de la classe OpenAI
                openai.api_key = self.openai_api_key
                self.clients[LLMProvider.OPENAI] = openai
                logger.info("Client OpenAI initialisé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}")
            
        # Initialiser Anthropic si la clé est disponible
        if self.anthropic_api_key:
            try:
                self.clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("Client Anthropic initialisé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du client Anthropic: {str(e)}")
                
        logger.info(f"Fournisseurs disponibles: {', '.join([p.value for p in self.clients.keys()])}")
    
    def get_client(self, provider: Optional[LLMProvider] = None):
        """Récupère le client pour le fournisseur spécifié ou le fournisseur par défaut"""
        provider = provider or self.default_provider
        
        if provider not in self.clients:
            raise ValueError(f"Fournisseur LLM non disponible: {provider}")
            
        return self.clients[provider]
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Récupère la liste des fournisseurs disponibles"""
        return list(self.clients.keys())
    
    def is_provider_available(self, provider: LLMProvider) -> bool:
        """Vérifie si un fournisseur est disponible"""
        return provider in self.clients


class LLMService:
    """Service pour interagir avec les modèles de langage"""
    
    def __init__(self, llm_factory: LLMFactory = None):
        self.llm_factory = llm_factory or LLMFactory()
        
        # Modèles par défaut pour chaque fournisseur
        self.default_models = {
            LLMProvider.GROQ: "llama3-70b-8192",
            LLMProvider.OPENAI: "gpt-4o",
            LLMProvider.ANTHROPIC: "claude-3-opus-20240229"
        }
        
    async def generate_text(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None
    ) -> str:
        """Génère du texte à partir d'un prompt"""
        
        provider = provider or self.llm_factory.default_provider
        model = model or self.default_models.get(provider)
        
        if not self.llm_factory.is_provider_available(provider):
            logger.warning(f"Fournisseur LLM non disponible: {provider}")
            raise ValueError(f"Fournisseur LLM non disponible: {provider}")
        
        client = self.llm_factory.get_client(provider)
        
        try:
            logger.info(f"Génération de texte avec {provider}, modèle: {model}, température: {temperature}")
            
            if provider == LLMProvider.GROQ:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message} if system_message else {"role": "system", "content": "Vous êtes un assistant juridique expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return completion.choices[0].message.content
                
            elif provider == LLMProvider.OPENAI:
                # Pour OpenAI ancienne version
                completion = client.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message} if system_message else {"role": "system", "content": "Vous êtes un assistant juridique expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return completion.choices[0].message.content
                
            elif provider == LLMProvider.ANTHROPIC:
                message = client.messages.create(
                    model=model,
                    system=system_message if system_message else "Vous êtes un assistant juridique expert.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return message.content[0].text
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de texte avec {provider}: {str(e)}")
            
            # En cas d'erreur, essayer un autre fournisseur si disponible
            available_providers = self.llm_factory.get_available_providers()
            if provider in available_providers:
                available_providers.remove(provider)
                
            if available_providers:
                fallback_provider = available_providers[0]
                logger.info(f"Tentative de fallback avec le fournisseur: {fallback_provider}")
                return await self.generate_text(
                    prompt=prompt,
                    provider=fallback_provider,
                    model=self.default_models.get(fallback_provider),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_message=system_message
                )
            else:
                raise ValueError(f"Erreur lors de la génération de texte et aucun fournisseur de secours disponible: {str(e)}")
    
    async def get_embedding(
        self,
        text: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None
    ) -> List[float]:
        """Génère un embedding vectoriel à partir d'un texte"""
        
        provider = provider or self.llm_factory.default_provider
        
        if provider == LLMProvider.OPENAI:
            try:
                model = model or "text-embedding-3-small"
                client = self.llm_factory.get_client(provider)
                logger.info(f"Génération d'embedding avec OpenAI, modèle: {model}")
                response = client.Embedding.create(
                    model=model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Erreur lors de la génération d'embedding avec OpenAI: {str(e)}")
                raise
                
        elif provider == LLMProvider.GROQ:
            # Groq n'a pas d'API d'embedding native, fallback possible vers OpenAI
            if self.llm_factory.is_provider_available(LLMProvider.OPENAI):
                logger.info("Groq ne supporte pas les embeddings, fallback vers OpenAI")
                return await self.get_embedding(text, LLMProvider.OPENAI)
        
        # Fallback si on n'a aucune solution
        logger.error(f"Embeddings non disponibles pour le fournisseur {provider}")
        raise ValueError(f"Embeddings non disponibles pour le fournisseur {provider}")
    
    async def extract_clauses(
        self,
        document_text: str,
        document_type: str,
        provider: Optional[LLMProvider] = None
    ) -> List[Dict[str, Any]]:
        """Extrait les clauses d'un document juridique"""
        
        logger.info(f"Extraction des clauses d'un document de type {document_type}")
        
        system_message = (
            "Vous êtes un expert juridique spécialisé dans l'analyse de contrats. "
            "Votre tâche est d'extraire TOUTES les clauses importantes du document fourni, même si elles "
            "sont implicites ou peu formalisées. Si le document ne contient pas de clauses explicites, "
            "identifiez les obligations, les droits et les restrictions implicites.\n\n"
            "Vous devez identifier le type de chaque clause parmi les options suivantes EXACTEMENT:\n"
            "- obligation\n"
            "- restriction\n"
            "- right\n"
            "- termination\n"
            "- confidentiality\n"
            "- intellectual_property\n"
            "- liability\n"
            "- payment\n"
            "- duration\n"
            "- other\n\n"
            "Le niveau de risque doit être un nombre entier entre 1 et 5, où:\n"
            "1 = Très faible\n"
            "2 = Faible\n"
            "3 = Moyen\n"
            "4 = Élevé\n"
            "5 = Très élevé\n"
        )
        
        # On construit la partie JSON sans f-string pour éviter les accolades non échappées
        json_instructions = (
            "Répondez au format JSON suivant:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Titre de la clause\",\n"
            "    \"content\": \"Contenu exact de la clause\",\n"
            "    \"type\": \"type_de_clause\", // UNIQUEMENT un des types exacts mentionnés\n"
            "    \"risk_level\": niveau_de_risque, // UNIQUEMENT un nombre entier entre 1 et 5\n"
            "    \"analysis\": \"Analyse juridique de la clause\"\n"
            "  },\n"
            "  ...\n"
            "]"
        )
        
        # Ici on peut utiliser une f-string uniquement pour les variables, 
        # et la partie JSON est concaténée sous forme de string classique
        prompt = (
            f"Analysez le document juridique suivant de type {document_type} et extrayez les clauses importantes.\n"
            "Pour chaque clause, fournissez:\n"
            "1. Un titre descriptif\n"
            "2. Le contenu exact de la clause\n"
            "3. Le type de clause (UNIQUEMENT un de ces termes exacts: obligation, restriction, right, termination, confidentiality, intellectual_property, liability, payment, duration, other)\n"
            "4. Le niveau de risque (UNIQUEMENT un nombre entier entre 1 et 5)\n"
            "5. Une analyse juridique de la clause\n\n"
            "Document:\n"
            f"{document_text}\n\n"
            "Si le document ne contient pas de clauses explicites, identifiez les éléments implicites.\n\n"
        ) + json_instructions
        
        result = await self.generate_text(
            prompt=prompt,
            provider=provider,
            system_message=system_message,
            temperature=0.3,
            max_tokens=4000
        )
        
        # Extraire le JSON de la réponse
        try:
            start_idx = result.find('[')
            end_idx = result.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                logger.info(f"Extraction réussie: {len(parsed_result)} clauses trouvées")
                return parsed_result
            else:
                # Fallback: essayer de parser toute la réponse
                parsed_result = json.loads(result)
                logger.info(f"Extraction réussie (fallback): {len(parsed_result)} clauses trouvées")
                return parsed_result
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors du parsing JSON des clauses: {str(e)}")
            logger.debug(f"Réponse brute: {result[:500]}...")
            return []
    
    async def generate_recommendations(
        self,
        clauses: List[Dict[str, Any]],
        document_type: str,
        provider: Optional[LLMProvider] = None
    ) -> List[Dict[str, Any]]:
        """Génère des recommandations basées sur les clauses extraites"""
        
        logger.info(f"Génération des recommandations pour un document de type {document_type}")
        
        system_message = (
            "Vous êtes un expert juridique spécialisé dans l'analyse de contrats.\n"
            "Votre tâche est de générer des recommandations pertinentes basées sur les clauses extraites d'un document juridique.\n\n"
            "Les priorités doivent être exprimées en nombres entiers avec:\n"
            "1 = Basse priorité\n"
            "2 = Priorité moyenne\n"
            "3 = Haute priorité\n"
        )
        
        # Convertir la liste de clauses en texte
        clauses_text = json.dumps(clauses, ensure_ascii=False, indent=2)
        
        # Instructions JSON
        json_instructions = (
            "Répondez au format JSON suivant:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Titre de la recommandation\",\n"
            "    \"description\": \"Description détaillée\",\n"
            "    \"priority\": niveau_de_priorité, // 1, 2 ou 3\n"
            "    \"suggested_text\": \"Texte suggéré (si applicable)\",\n"
            "    \"related_clauses\": [\"Titre de la clause 1\", \"Titre de la clause 2\", ...]\n"
            "  },\n"
            "  ...\n"
            "]"
        )
        
        prompt = (
            f"Sur la base des clauses suivantes extraites d'un document juridique de type {document_type}, "
            "générez des recommandations pertinentes pour améliorer le contrat ou atténuer les risques identifiés.\n\n"
            "Clauses extraites:\n"
            f"{clauses_text}\n\n"
            "Pour chaque recommandation, fournissez:\n"
            "1. Un titre descriptif\n"
            "2. Une description détaillée\n"
            "3. Une priorité (1, 2 ou 3)\n"
            "4. Un texte suggéré (si applicable)\n"
            "5. Les titres des clauses concernées\n\n"
            "Si le document manque de clauses essentielles, suggérez l'ajout de ces clauses.\n\n"
        ) + json_instructions
        
        result = await self.generate_text(
            prompt=prompt,
            provider=provider,
            system_message=system_message,
            temperature=0.4,
            max_tokens=4000
        )
        
        # Extraire le JSON
        try:
            start_idx = result.find('[')
            end_idx = result.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                logger.info(f"Génération de recommandations réussie: {len(parsed_result)} recommandations générées")
                return parsed_result
            else:
                parsed_result = json.loads(result)
                logger.info(f"Génération de recommandations réussie (fallback): {len(parsed_result)} recommandations générées")
                return parsed_result
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors du parsing JSON des recommandations: {str(e)}")
            logger.debug(f"Réponse brute: {result[:500]}...")
            return []
    
    async def identify_risks(
        self,
        clauses: List[Dict[str, Any]],
        document_type: str,
        provider: Optional[LLMProvider] = None
    ) -> List[Dict[str, Any]]:
        """Identifie les risques juridiques basés sur les clauses extraites"""
        
        logger.info(f"Identification des risques pour un document de type {document_type}")
        
        system_message = (
            "Vous êtes un expert juridique spécialisé dans l'analyse de risques contractuels.\n"
            "Votre tâche est d'identifier et d'évaluer les risques juridiques potentiels basés sur les clauses extraites.\n\n"
            "Les niveaux de risque doivent être un nombre entier entre 1 et 5:\n"
            "1 = Très faible\n"
            "2 = Faible\n"
            "3 = Moyen\n"
            "4 = Élevé\n"
            "5 = Très élevé\n"
        )
        
        clauses_text = json.dumps(clauses, ensure_ascii=False, indent=2)
        
        # Pour rappel, la question semble mélanger des consignes de "risks" et "recommendations".
        # On met un bloc JSON distinct pour clarifier. 
        # Adaptez éventuellement selon votre logique métier.
        json_instructions = (
            "Répondez au format JSON suivant:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Titre du risque\",\n"
            "    \"description\": \"Description du risque\",\n"
            "    \"level\": niveau_de_risque, // 1 à 5\n"
            "    \"impact\": \"Impact potentiel\",\n"
            "    \"mitigation\": \"Pistes de mitigation (facultatif)\"\n"
            "  },\n"
            "  ...\n"
            "]"
        )
        
        # Exemple de prompt : On adapte le texte pour parler spécifiquement des risques
        prompt = (
            f"Sur la base des clauses suivantes extraites d'un document juridique de type {document_type}, "
            "identifiez et évaluez les risques juridiques potentiels.\n\n"
            "Clauses extraites:\n"
            f"{clauses_text}\n\n"
            "Pour chaque risque, fournissez:\n"
            "1. Un titre descriptif\n"
            "2. Une description détaillée\n"
            "3. Un niveau de risque (1 à 5)\n"
            "4. Un impact potentiel\n"
            "5. Des pistes de mitigation (facultatif)\n\n"
        ) + json_instructions
        
        result = await self.generate_text(
            prompt=prompt,
            provider=provider,
            system_message=system_message,
            temperature=0.3,
            max_tokens=4000
        )
        
        try:
            start_idx = result.find('[')
            end_idx = result.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                logger.info(f"Identification des risques réussie: {len(parsed_result)} risques identifiés")
                return parsed_result
            else:
                parsed_result = json.loads(result)
                logger.info(f"Identification des risques réussie (fallback): {len(parsed_result)} risques identifiés")
                return parsed_result
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors du parsing JSON des risques: {str(e)}")
            logger.debug(f"Réponse brute: {result[:500]}...")
            return []
    
    async def generate_summary(
        self,
        document_text: str,
        clauses: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        document_type: str,
        provider: Optional[LLMProvider] = None
    ) -> str:
        """Génère un résumé du document et de l'analyse"""
        
        logger.info(f"Génération du résumé pour un document de type {document_type}")
        
        system_message = (
            "Vous êtes un expert juridique spécialisé dans la synthèse de documents contractuels. "
            "Votre tâche est de générer un résumé concis mais complet d'un document juridique et de son analyse. "
            "Le résumé doit être clair, précis et accessible à des non-juristes tout en restant juridiquement rigoureux."
        )
        
        # Convertir les clauses et risques en texte pour le prompt
        clauses_text = json.dumps(clauses, ensure_ascii=False, indent=2)
        risks_text = json.dumps(risks, ensure_ascii=False, indent=2)
        
        # On limite l'aperçu du document à 2000 caractères, comme le code initial
        prompt_introduction = (
            f"Générez un résumé concis mais complet du document juridique de type {document_type} et de son analyse.\n\n"
            "Le résumé doit inclure:\n"
            "1. Une vue d'ensemble du document\n"
            "2. Les principales clauses et leurs implications\n"
            "3. Les risques majeurs identifiés\n"
            "4. Une conclusion sur la qualité juridique du document\n\n"
            "Document (aperçu) :\n"
            f"{document_text[:2000]}...\n\n"
        )
        
        prompt_data = (
            f"Clauses extraites:\n{clauses_text}\n\n"
            f"Risques identifiés:\n{risks_text}\n\n"
            "Utilisez le format Markdown pour structurer votre résumé (titres, sous-titres, puces). "
            "Le résumé doit être clair, concis et rigoureux.\n"
        )
        
        prompt = prompt_introduction + prompt_data
        
        result = await self.generate_text(
            prompt=prompt,
            provider=provider,
            system_message=system_message,
            temperature=0.5,
            max_tokens=2000
        )
        
        logger.info(f"Génération du résumé réussie: {len(result)} caractères")
        return result

# Architecture et workflows du PoC d'analyse de documents juridiques

Ce document décrit l'architecture technique et les workflows implémentés dans le PoC d'analyse de documents juridiques.

## Architecture technique

Le PoC est construit selon une architecture API-first avec les composants suivants :

### Backend (FastAPI)

Le backend est développé avec FastAPI, un framework Python moderne pour la création d'API RESTful. Il est organisé en plusieurs couches :

1. **Couche API** : Définit les endpoints REST et gère les requêtes HTTP
   - `routers/documents.py` : Gestion des documents juridiques
   - `routers/analysis.py` : Gestion des analyses de documents
   - `routers/precedents.py` : Recherche de précédents juridiques

2. **Couche Service** : Contient la logique métier
   - `services/document_service.py` : Service pour la gestion des documents
   - `services/analysis_service.py` : Service pour la gestion des analyses
   - `services/vector_service.py` : Service pour la recherche vectorielle

3. **Couche Modèle** : Définit les structures de données
   - `models/document.py` : Modèles pour les documents
   - `models/analysis.py` : Modèles pour les analyses, clauses, recommandations et risques

4. **Couche Workflow** : Implémente les patterns de workflow
   - `workflows/orchestrator.py` : Orchestrateur pour les workflows d'analyse

5. **Couche LLM** : Abstraction pour les modèles de langage
   - `llm/llm_factory.py` : Factory pour créer des instances de LLM (Groq, OpenAI, Anthropic)

### Frontend (Vue.js)

Le frontend est développé avec Vue.js, un framework JavaScript progressif pour la création d'interfaces utilisateur. Il est organisé comme suit :

1. **Composants** : Éléments réutilisables de l'interface
   - `components/DocumentUpload.vue` : Téléchargement de documents
   - `components/AnalysisResults.vue` : Affichage des résultats d'analyse
   - `components/ClausesList.vue` : Liste des clauses extraites
   - `components/Recommendations.vue` : Liste des recommandations

2. **Vues** : Pages principales de l'application
   - `views/Home.vue` : Page d'accueil
   - `views/Analysis.vue` : Page d'analyse
   - `views/History.vue` : Historique des analyses

3. **Services** : Communication avec l'API
   - `services/ApiService.js` : Service pour communiquer avec le backend

4. **Store** : Gestion de l'état global
   - `store/index.js` : Store Vuex pour la gestion de l'état

### Bases de données

Le PoC utilise trois bases de données différentes :

1. **MongoDB** : Stockage des documents et métadonnées
   - Collections : documents, analyses

2. **Qdrant** : Base de données vectorielle pour la recherche de précédents juridiques
   - Collection : legal_precedents

3. **Redis** : Stockage du contexte et cache
   - Utilisé pour stocker temporairement les contextes d'analyse

### Proxy inverse (Nginx)

Nginx sert de proxy inverse pour :
- Servir le frontend
- Rediriger les requêtes API vers le backend
- Gérer les uploads de fichiers

## Workflows d'analyse

Le PoC implémente plusieurs patterns de workflow pour l'analyse de documents juridiques :

### 1. Chaînage de prompts

Le processus d'analyse est divisé en étapes séquentielles :

1. Extraction du texte du document
2. Extraction des clauses
3. Génération de recommandations
4. Identification des risques
5. Recherche de précédents
6. Génération d'un résumé

Chaque étape utilise les résultats de l'étape précédente pour affiner l'analyse.

### 2. Gating (Portes)

Des contrôles conditionnels sont implémentés à différentes étapes :

- Vérification du type de fichier avant l'extraction
- Validation du type de document avant l'analyse
- Vérification de la qualité des clauses extraites avant de générer des recommandations

### 3. Routage

L'analyse est adaptée en fonction du type de document :

- Contrats de travail
- Contrats de prestation
- Contrats de partenariat
- Autres types de contrats

Chaque type de document a ses propres critères d'analyse et points d'attention.

### 4. Parallélisation

Certaines tâches sont exécutées en parallèle pour optimiser les performances :

- Génération de recommandations et identification des risques
- Recherche de précédents pour différentes clauses
- Génération du résumé pendant la recherche de précédents

La méthode `parallel_analysis_workflow` dans l'orchestrateur implémente cette parallélisation.

### 5. Orchestrateur-Ouvriers

L'orchestrateur (`workflows/orchestrator.py`) décompose l'analyse en tâches plus petites et les distribue :

- Extraction de texte
- Analyse de clauses spécifiques
- Recherche de précédents
- Génération de recommandations

### 6. Évaluateur-Optimiseur

Une boucle de qualité est implémentée pour améliorer les résultats :

1. Génération initiale des résultats
2. Évaluation de la qualité des résultats
3. Optimisation des résultats si nécessaire

## Flux de données

Le flux de données dans le système est le suivant :

1. L'utilisateur télécharge un document juridique via l'interface web
2. Le document est stocké dans le système de fichiers et ses métadonnées dans MongoDB
3. L'utilisateur démarre l'analyse du document
4. L'orchestrateur exécute le workflow d'analyse :
   - Extraction du texte du document
   - Utilisation des LLM pour extraire les clauses
   - Utilisation des LLM pour générer des recommandations
   - Utilisation des LLM pour identifier les risques
   - Recherche de précédents similaires dans Qdrant
   - Génération d'un résumé
5. Les résultats de l'analyse sont stockés dans MongoDB
6. L'utilisateur peut consulter les résultats via l'interface web

## Gestion des erreurs

Le système implémente plusieurs mécanismes de gestion des erreurs :

1. **Retry automatique** : En cas d'échec d'un appel LLM, le système tente automatiquement d'utiliser un autre fournisseur
2. **Logging détaillé** : Toutes les erreurs sont enregistrées avec des informations contextuelles
3. **Statut d'analyse** : Le statut de l'analyse est mis à jour en temps réel pour informer l'utilisateur
4. **Possibilité de relance** : Les analyses échouées peuvent être relancées manuellement

## Sécurité

Plusieurs mesures de sécurité sont implémentées :

1. **Validation des fichiers** : Vérification du type et de la taille des fichiers téléchargés
2. **Sanitization des entrées** : Nettoyage des entrées utilisateur
3. **Isolation des conteneurs** : Chaque service s'exécute dans son propre conteneur Docker
4. **Variables d'environnement** : Les clés API et autres informations sensibles sont stockées dans des variables d'environnement

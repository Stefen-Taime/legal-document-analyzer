#!/bin/bash

# Script de test pour vérifier le bon fonctionnement du PoC d'analyse de documents juridiques

echo "=== Tests du PoC d'analyse de documents juridiques ==="
echo ""

# Vérifier que Docker et Docker Compose sont installés
echo "Vérification de Docker et Docker Compose..."
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

echo "Docker et Docker Compose sont installés."
echo ""

# Vérifier que les fichiers de configuration existent
echo "Vérification des fichiers de configuration..."
if [ ! -f "docker-compose.yml" ]; then
    echo "Le fichier docker-compose.yml n'existe pas."
    exit 1
fi

if [ ! -f "nginx/nginx.conf" ]; then
    echo "Le fichier nginx/nginx.conf n'existe pas."
    exit 1
fi

if [ ! -f ".env.example" ]; then
    echo "Le fichier .env.example n'existe pas."
    exit 1
fi

echo "Tous les fichiers de configuration sont présents."
echo ""

# Créer le fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo "Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "Fichier .env créé. Veuillez le modifier pour ajouter vos clés API si nécessaire."
    echo ""
fi

# Vérifier que les Dockerfiles existent
echo "Vérification des Dockerfiles..."
if [ ! -f "api/Dockerfile" ]; then
    echo "Le fichier api/Dockerfile n'existe pas."
    exit 1
fi

if [ ! -f "frontend/Dockerfile" ]; then
    echo "Le fichier frontend/Dockerfile n'existe pas."
    exit 1
fi

echo "Tous les Dockerfiles sont présents."
echo ""

# Vérifier que les scripts d'initialisation existent
echo "Vérification des scripts d'initialisation..."
if [ ! -f "scripts/seed_vector_db.sh" ]; then
    echo "Le script scripts/seed_vector_db.sh n'existe pas."
    exit 1
fi

if [ ! -f "scripts/seed_vector_db.py" ]; then
    echo "Le script scripts/seed_vector_db.py n'existe pas."
    exit 1
fi

echo "Tous les scripts d'initialisation sont présents."
echo ""

# Vérifier que les répertoires nécessaires existent
echo "Vérification des répertoires..."
for dir in api/app frontend/src nginx qdrant scripts; do
    if [ ! -d "$dir" ]; then
        echo "Le répertoire $dir n'existe pas."
        exit 1
    fi
done

echo "Tous les répertoires nécessaires sont présents."
echo ""

# Vérifier les fichiers principaux du backend
echo "Vérification des fichiers principaux du backend..."
for file in api/app/main.py api/app/models/document.py api/app/models/analysis.py api/app/routers/documents.py api/app/routers/analysis.py api/app/services/document_service.py api/app/services/analysis_service.py api/app/services/vector_service.py api/app/llm/llm_factory.py api/app/workflows/orchestrator.py; do
    if [ ! -f "$file" ]; then
        echo "Le fichier $file n'existe pas."
        exit 1
    fi
done

echo "Tous les fichiers principaux du backend sont présents."
echo ""

# Vérifier les fichiers principaux du frontend
echo "Vérification des fichiers principaux du frontend..."
for file in frontend/src/main.js frontend/src/App.vue frontend/src/router/index.js frontend/src/store/index.js frontend/src/services/ApiService.js frontend/src/components/DocumentUpload.vue frontend/src/components/AnalysisResults.vue frontend/src/views/Home.vue frontend/src/views/Analysis.vue frontend/src/views/History.vue; do
    if [ ! -f "$file" ]; then
        echo "Le fichier $file n'existe pas."
        exit 1
    fi
done

echo "Tous les fichiers principaux du frontend sont présents."
echo ""

echo "=== Tous les tests de vérification des fichiers ont réussi ! ==="
echo ""
echo "Pour démarrer l'application, exécutez la commande suivante :"
echo "docker-compose up -d"
echo ""
echo "Pour arrêter l'application, exécutez la commande suivante :"
echo "docker-compose down"
echo ""
echo "Pour visualiser les logs, exécutez la commande suivante :"
echo "docker-compose logs -f"
echo ""
echo "L'application sera accessible à l'adresse suivante :"
echo "http://localhost"
echo ""
echo "=== Fin des tests ==="

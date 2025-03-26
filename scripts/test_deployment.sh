#!/bin/bash

# Script de test pour vérifier le déploiement complet avec Docker Compose

echo "=== Test de déploiement complet du PoC d'analyse de documents juridiques ==="
echo ""

# Vérifier que Docker et Docker Compose sont installés
echo "Vérification de Docker et Docker Compose..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

echo "✅ Docker et Docker Compose sont installés."
echo ""

# Vérifier que le fichier .env existe
if [ ! -f ".env" ]; then
    echo "⚠️ Le fichier .env n'existe pas. Création à partir de .env.example..."
    cp .env.example .env
    echo "✅ Fichier .env créé. Veuillez le modifier pour ajouter vos clés API si nécessaire."
    echo ""
fi

# Arrêter les conteneurs existants
echo "Arrêt des conteneurs existants..."
docker-compose down
echo "✅ Conteneurs arrêtés."
echo ""

# Démarrer les conteneurs
echo "Démarrage des conteneurs..."
docker-compose up -d
echo "✅ Conteneurs démarrés."
echo ""

# Attendre que les services soient prêts
echo "Attente du démarrage des services..."
echo "Cela peut prendre quelques minutes..."

# Fonction pour vérifier si un service est prêt
check_service() {
    local service=$1
    local max_attempts=$2
    local attempt=1
    
    echo -n "Vérification du service $service: "
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep $service | grep -q "Up"; then
            echo "✅ Prêt!"
            return 0
        fi
        echo -n "."
        sleep 5
        attempt=$((attempt+1))
    done
    
    echo "❌ Non disponible après $max_attempts tentatives."
    return 1
}

# Vérifier chaque service
check_service "legal-analyzer-mongodb" 12 || exit 1
check_service "legal-analyzer-redis" 12 || exit 1
check_service "legal-analyzer-qdrant" 12 || exit 1
check_service "legal-analyzer-api" 24 || exit 1
check_service "legal-analyzer-frontend" 12 || exit 1
check_service "legal-analyzer-nginx" 12 || exit 1

echo ""
echo "Tous les services sont démarrés!"
echo ""

# Vérifier l'accès à l'API
echo "Vérification de l'accès à l'API..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/api/health" || echo "000")

if [ "$API_HEALTH" -eq 200 ]; then
    echo "✅ L'API est accessible (code 200)."
else
    echo "❌ L'API n'est pas accessible (code $API_HEALTH)."
    echo "Vérifiez les logs avec: docker-compose logs api"
    exit 1
fi
echo ""

# Vérifier l'accès au frontend
echo "Vérification de l'accès au frontend..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/" || echo "000")

if [ "$FRONTEND_HEALTH" -eq 200 ]; then
    echo "✅ Le frontend est accessible (code 200)."
else
    echo "❌ Le frontend n'est pas accessible (code $FRONTEND_HEALTH)."
    echo "Vérifiez les logs avec: docker-compose logs frontend"
    exit 1
fi
echo ""

# Afficher les logs des conteneurs
echo "Affichage des logs des conteneurs (dernières 10 lignes)..."
echo ""
echo "=== Logs de l'API ==="
docker-compose logs --tail=10 api
echo ""
echo "=== Logs du frontend ==="
docker-compose logs --tail=10 frontend
echo ""
echo "=== Logs de Nginx ==="
docker-compose logs --tail=10 nginx
echo ""

echo "=== Test de déploiement complet réussi ! ==="
echo ""
echo "L'application est accessible à l'adresse: http://localhost"
echo ""
echo "Pour arrêter l'application, exécutez: docker-compose down"
echo "Pour voir tous les logs, exécutez: docker-compose logs -f"
echo ""
echo "=== Fin du test de déploiement ==="

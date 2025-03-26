#!/bin/bash

# Script de test pour le PoC d'analyse de documents juridiques

echo "Exécution des tests pour le PoC d'analyse de documents juridiques..."

# Vérifier si les conteneurs sont en cours d'exécution
if ! docker-compose ps | grep -q "legal-analyzer-api"; then
    echo "Les conteneurs ne sont pas en cours d'exécution. Démarrage des conteneurs..."
    docker-compose up -d
    echo "Attente du démarrage complet des services..."
    sleep 10
fi

# Exécuter les tests unitaires du backend
echo "Exécution des tests unitaires du backend..."
docker-compose exec api pytest -v

# Vérifier l'état de santé de l'API
echo "Vérification de l'état de santé de l'API..."
curl -s http://localhost/api/health | grep -q "ok" && echo "API en bon état" || echo "API en erreur"

# Vérifier l'état de santé de la base de données vectorielle
echo "Vérification de l'état de santé de Qdrant..."
curl -s http://localhost:6333/health | grep -q "ok" && echo "Qdrant en bon état" || echo "Qdrant en erreur"

# Vérifier l'accès au frontend
echo "Vérification de l'accès au frontend..."
curl -s -I http://localhost | grep -q "200 OK" && echo "Frontend accessible" || echo "Frontend inaccessible"

echo "Tests terminés."

#!/bin/bash

# Script de vérification finale pour le PoC d'analyse de documents juridiques

echo "=== Vérification finale du PoC d'analyse de documents juridiques ==="
echo ""

# Vérifier que tous les fichiers nécessaires sont présents
echo "Vérification des fichiers essentiels..."
./scripts/test_setup.sh
if [ $? -ne 0 ]; then
    echo "❌ La vérification des fichiers a échoué. Veuillez corriger les erreurs avant de continuer."
    exit 1
fi
echo "✅ Tous les fichiers essentiels sont présents."
echo ""

# Vérifier que la documentation est complète
echo "Vérification de la documentation..."
for doc in README.md docs/architecture.md docs/installation.md docs/fonctionnalites.md; do
    if [ ! -f "$doc" ]; then
        echo "❌ Le document $doc est manquant."
        exit 1
    fi
done
echo "✅ La documentation est complète."
echo ""

# Créer un fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo "Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "⚠️ Fichier .env créé. Veuillez le modifier pour ajouter vos clés API avant de déployer l'application."
    echo ""
fi

# Créer une archive du projet
echo "Création d'une archive du projet..."
VERSION=$(date +"%Y%m%d")
ARCHIVE_NAME="legal-document-analyzer-v$VERSION.zip"

# Exclure les fichiers non nécessaires
zip -r "$ARCHIVE_NAME" . -x "*.git*" "*.zip" "*.DS_Store" "node_modules/*" "__pycache__/*" "*.pyc"

echo "✅ Archive créée : $ARCHIVE_NAME"
echo ""

# Afficher les instructions finales
echo "=== Instructions pour la démonstration ==="
echo ""
echo "1. Déploiement de l'application :"
echo "   docker-compose up -d"
echo ""
echo "2. Vérification du déploiement :"
echo "   ./scripts/test_deployment.sh"
echo ""
echo "3. Accès à l'application :"
echo "   Frontend : http://localhost"
echo "   Documentation API : http://localhost/api/docs"
echo ""
echo "4. Test des fonctionnalités :"
echo "   - Téléchargement d'un document juridique"
echo "   - Analyse du document"
echo "   - Consultation des clauses extraites et des recommandations"
echo "   - Recherche de précédents juridiques"
echo "   - Exportation des résultats"
echo ""
echo "5. Arrêt de l'application :"
echo "   docker-compose down"
echo ""
echo "=== Livraison finale terminée ! ==="

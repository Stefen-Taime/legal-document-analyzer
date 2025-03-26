#!/bin/bash

# Script de test pour vérifier le fonctionnement du frontend

echo "=== Tests du frontend du PoC d'analyse de documents juridiques ==="
echo ""

# Vérifier que curl est installé
if ! command -v curl &> /dev/null; then
    echo "curl n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# URL de base du frontend
FRONTEND_URL="http://localhost"

# Test d'accès à la page d'accueil
echo "Test d'accès à la page d'accueil..."
HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/")
if [ "$HOME_RESPONSE" -eq 200 ]; then
    echo "✅ La page d'accueil est accessible (code 200)."
else
    echo "❌ La page d'accueil n'est pas accessible (code $HOME_RESPONSE)."
    echo "Assurez-vous que l'application est démarrée avec docker-compose up -d"
    exit 1
fi
echo ""

# Test d'accès aux ressources statiques (CSS, JS)
echo "Test d'accès aux ressources statiques..."
CSS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/css/app.css" || echo "404")
JS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/js/app.js" || echo "404")

if [ "$CSS_RESPONSE" -eq 200 ] || [ "$JS_RESPONSE" -eq 200 ]; then
    echo "✅ Les ressources statiques sont accessibles."
else
    echo "⚠️ Les ressources statiques ne sont pas accessibles directement."
    echo "   Cela peut être normal si elles sont intégrées dans le bundle."
fi
echo ""

# Test d'accès à la page d'analyse
echo "Test d'accès à la page d'analyse..."
ANALYSIS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/analysis")
if [ "$ANALYSIS_RESPONSE" -eq 200 ]; then
    echo "✅ La page d'analyse est accessible (code 200)."
else
    echo "⚠️ La page d'analyse n'est pas accessible directement (code $ANALYSIS_RESPONSE)."
    echo "   Cela peut être normal si le routage est géré côté client."
fi
echo ""

# Test d'accès à la page d'historique
echo "Test d'accès à la page d'historique..."
HISTORY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/history")
if [ "$HISTORY_RESPONSE" -eq 200 ]; then
    echo "✅ La page d'historique est accessible (code 200)."
else
    echo "⚠️ La page d'historique n'est pas accessible directement (code $HISTORY_RESPONSE)."
    echo "   Cela peut être normal si le routage est géré côté client."
fi
echo ""

echo "=== Tests du frontend terminés ==="
echo ""
echo "Note: Ces tests vérifient uniquement l'accessibilité des pages."
echo "Pour des tests plus approfondis, utilisez un navigateur ou des outils comme Cypress."
echo ""
echo "Pour tester manuellement l'interface utilisateur, accédez à:"
echo "${FRONTEND_URL}"
echo ""
echo "=== Fin des tests du frontend ==="

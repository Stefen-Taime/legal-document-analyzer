#!/bin/bash

# Script de test pour vérifier le fonctionnement de l'API

echo "=== Tests de l'API du PoC d'analyse de documents juridiques ==="
echo ""

# Vérifier que curl est installé
if ! command -v curl &> /dev/null; then
    echo "curl n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# URL de base de l'API
API_URL="http://localhost/api"

# Test du endpoint de santé
echo "Test du endpoint de santé..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    echo "✅ Le endpoint de santé répond correctement (code 200)."
else
    echo "❌ Le endpoint de santé ne répond pas correctement (code $HEALTH_RESPONSE)."
    echo "Assurez-vous que l'application est démarrée avec docker-compose up -d"
    exit 1
fi
echo ""

# Test de téléchargement d'un document (création d'un document de test)
echo "Création d'un document de test..."
TEST_DOC_PATH="/tmp/test_contract.txt"
cat > "$TEST_DOC_PATH" << EOF
CONTRAT DE PRESTATION DE SERVICES

Entre les soussignés :
La société XYZ, représentée par M. Dupont, ci-après dénommée "le Prestataire"
Et
La société ABC, représentée par Mme Martin, ci-après dénommée "le Client"

Article 1 - Objet du contrat
Le Prestataire s'engage à fournir au Client des services de conseil en informatique.

Article 2 - Durée du contrat
Le présent contrat est conclu pour une durée de 12 mois à compter de sa signature.

Article 3 - Rémunération
Le Client s'engage à verser au Prestataire la somme de 10 000 euros HT par mois.

Article 4 - Confidentialité
Le Prestataire s'engage à maintenir confidentielle toute information obtenue dans le cadre de ce contrat, et ce pour une durée illimitée.

Article 5 - Clause de non-concurrence
Le Prestataire s'engage à ne pas travailler pour un concurrent du Client pendant la durée du contrat et pour une période de 5 ans après la fin du contrat, dans toute l'Europe.

Article 6 - Résiliation
Le Client peut résilier le contrat à tout moment sans préavis ni indemnité.

Article 7 - Responsabilité
La responsabilité du Prestataire est limitée à 10% du montant total du contrat, quels que soient les dommages causés.

Fait à Paris, le 25 mars 2025
EOF

echo "Test de téléchargement d'un document..."
UPLOAD_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -F "file=@$TEST_DOC_PATH" "${API_URL}/documents/upload")
if [ "$UPLOAD_RESPONSE" -eq 200 ] || [ "$UPLOAD_RESPONSE" -eq 201 ]; then
    echo "✅ Le téléchargement de document fonctionne correctement (code $UPLOAD_RESPONSE)."
else
    echo "❌ Le téléchargement de document ne fonctionne pas correctement (code $UPLOAD_RESPONSE)."
    exit 1
fi
echo ""

# Test de récupération de la liste des documents
echo "Test de récupération de la liste des documents..."
DOCUMENTS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/documents")
if [ "$DOCUMENTS_RESPONSE" -eq 200 ]; then
    echo "✅ La récupération de la liste des documents fonctionne correctement (code 200)."
else
    echo "❌ La récupération de la liste des documents ne fonctionne pas correctement (code $DOCUMENTS_RESPONSE)."
    exit 1
fi
echo ""

# Test de recherche de précédents juridiques
echo "Test de recherche de précédents juridiques..."
SEARCH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/precedents/search?query=clause%20de%20non-concurrence")
if [ "$SEARCH_RESPONSE" -eq 200 ]; then
    echo "✅ La recherche de précédents juridiques fonctionne correctement (code 200)."
else
    echo "❌ La recherche de précédents juridiques ne fonctionne pas correctement (code $SEARCH_RESPONSE)."
    exit 1
fi
echo ""

echo "=== Tous les tests de l'API ont réussi ! ==="
echo ""
echo "Note: Ces tests vérifient uniquement que les endpoints répondent correctement."
echo "Pour des tests plus approfondis, utilisez l'interface utilisateur ou des outils comme Postman."
echo ""
echo "=== Fin des tests de l'API ==="

# Nettoyage
rm -f "$TEST_DOC_PATH"

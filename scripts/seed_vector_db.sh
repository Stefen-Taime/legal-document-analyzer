#!/bin/bash

# Script pour initialiser la base de données vectorielle avec des précédents juridiques

# Vérifier que Qdrant est disponible
echo "Vérification de la disponibilité de Qdrant..."
until curl -s -f "http://qdrant:6333/health" > /dev/null; do
  echo "Qdrant n'est pas encore disponible, nouvelle tentative dans 5 secondes..."
  sleep 5
done
echo "Qdrant est disponible!"

# Chemin vers le fichier de données
DATA_FILE="/app/data/precedents.json"

# Vérifier si le fichier de données existe
if [ ! -f "$DATA_FILE" ]; then
  echo "Création du répertoire de données..."
  mkdir -p /app/data
  
  echo "Génération de données de précédents juridiques..."
  cat > "$DATA_FILE" << EOF
[
  {
    "title": "Clause de non-concurrence excessive",
    "description": "Une clause de non-concurrence a été jugée excessive car elle couvrait une zone géographique trop large et une durée déraisonnable sans compensation adéquate.",
    "type": "jurisprudence",
    "relevance": "haute",
    "source": "Cour de cassation, chambre sociale, 10 juillet 2002"
  },
  {
    "title": "Clause de confidentialité sans limite de temps",
    "description": "Une clause de confidentialité sans limite de temps a été jugée valide pour protéger des secrets commerciaux légitimes, mais doit être proportionnée aux intérêts protégés.",
    "type": "jurisprudence",
    "relevance": "moyenne",
    "source": "Cour d'appel de Paris, 25 septembre 2018"
  },
  {
    "title": "Clause de résiliation unilatérale abusive",
    "description": "Une clause permettant la résiliation unilatérale sans préavis raisonnable a été jugée abusive dans un contrat entre professionnels de force inégale.",
    "type": "jurisprudence",
    "relevance": "haute",
    "source": "Cour de cassation, chambre commerciale, 3 décembre 2013"
  },
  {
    "title": "Clause limitative de responsabilité disproportionnée",
    "description": "Une clause limitative de responsabilité a été invalidée car elle vidait le contrat de sa substance en exonérant le prestataire de ses obligations essentielles.",
    "type": "jurisprudence",
    "relevance": "haute",
    "source": "Cour de cassation, chambre commerciale, arrêt Chronopost, 22 octobre 1996"
  },
  {
    "title": "Clause d'exclusivité excessive",
    "description": "Une clause d'exclusivité de 5 ans sans possibilité de résiliation a été jugée contraire au droit de la concurrence et créant une dépendance économique excessive.",
    "type": "jurisprudence",
    "relevance": "moyenne",
    "source": "Autorité de la concurrence, décision n°18-D-04 du 20 février 2018"
  },
  {
    "title": "Clause de mobilité géographique imprécise",
    "description": "Une clause de mobilité ne précisant pas la zone géographique d'application a été jugée nulle car elle ne permettait pas au salarié de connaître l'étendue de son obligation.",
    "type": "jurisprudence",
    "relevance": "moyenne",
    "source": "Cour de cassation, chambre sociale, 7 juin 2006"
  },
  {
    "title": "Clause pénale manifestement excessive",
    "description": "Une clause pénale prévoyant une indemnité manifestement excessive peut être réduite par le juge, même d'office, au regard du préjudice effectivement subi.",
    "type": "jurisprudence",
    "relevance": "haute",
    "source": "Cour de cassation, 1ère chambre civile, 24 juillet 2019"
  },
  {
    "title": "Clause d'arbitrage dans un contrat de consommation",
    "description": "Une clause imposant l'arbitrage dans un contrat de consommation a été jugée abusive car elle prive le consommateur de son droit d'accès au juge étatique.",
    "type": "jurisprudence",
    "relevance": "moyenne",
    "source": "CJUE, 26 octobre 2006, Mostaza Claro"
  },
  {
    "title": "Clause de dédit-formation disproportionnée",
    "description": "Une clause de dédit-formation imposant le remboursement intégral des frais sans dégressivité temporelle a été jugée disproportionnée et partiellement invalidée.",
    "type": "jurisprudence",
    "relevance": "basse",
    "source": "Cour de cassation, chambre sociale, 21 mai 2008"
  },
  {
    "title": "Clause de non-sollicitation de clientèle",
    "description": "Une clause de non-sollicitation de clientèle a été validée car elle était limitée dans le temps et l'espace et ne constituait pas une restriction disproportionnée à la liberté de travail.",
    "type": "jurisprudence",
    "relevance": "moyenne",
    "source": "Cour de cassation, chambre commerciale, 11 septembre 2012"
  }
]
EOF
  echo "Fichier de données créé avec succès!"
fi

# Exécuter le script Python pour initialiser la base vectorielle
echo "Initialisation de la base vectorielle avec les précédents juridiques..."
python3 /app/scripts/seed_vector_db.py

echo "Initialisation terminée!"

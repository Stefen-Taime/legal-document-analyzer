#!/bin/bash

# Script d'installation et de configuration pour le PoC d'analyse de documents juridiques

echo "Installation du PoC d'analyse de documents juridiques..."

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Installation de Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker a été installé. Veuillez vous déconnecter et vous reconnecter pour appliquer les changements de groupe."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose n'est pas installé. Installation de Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose a été installé."
fi

# Créer le fichier .env à partir de .env.example
if [ ! -f .env ]; then
    echo "Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "Veuillez éditer le fichier .env pour configurer vos clés API et autres paramètres."
fi

# Construire et démarrer les conteneurs
echo "Construction et démarrage des conteneurs Docker..."
docker-compose up -d --build

echo "Installation terminée. L'application est accessible à l'adresse http://localhost"
echo "Documentation API: http://localhost/docs"
echo "Interface d'administration: http://localhost/admin"

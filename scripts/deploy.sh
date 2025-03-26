#!/bin/bash

# Script de déploiement automatisé pour le PoC d'analyse de documents juridiques
# Ce script permet de déployer l'application en production ou en environnement de test

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCÈS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Vérifier si Docker et Docker Compose sont installés
check_prerequisites() {
    print_message "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé. Installation en cours..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        print_warning "Veuillez vous déconnecter et vous reconnecter pour que les changements prennent effet."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé. Installation en cours..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    print_success "Tous les prérequis sont installés."
}

# Configurer les variables d'environnement
setup_environment() {
    print_message "Configuration de l'environnement..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_warning "Fichier .env créé à partir de .env.example."
        print_warning "Veuillez éditer le fichier .env pour configurer vos clés API et autres paramètres."
        
        # Demander à l'utilisateur s'il souhaite configurer les clés API maintenant
        read -p "Souhaitez-vous configurer les clés API maintenant? (o/n): " configure_keys
        
        if [[ $configure_keys == "o" || $configure_keys == "O" ]]; then
            read -p "Entrez votre clé API Groq (laissez vide si non disponible): " groq_key
            read -p "Entrez votre clé API OpenAI (laissez vide si non disponible): " openai_key
            read -p "Entrez votre clé API Anthropic (laissez vide si non disponible): " anthropic_key
            
            if [ ! -z "$groq_key" ]; then
                sed -i "s/GROQ_API_KEY=.*/GROQ_API_KEY=$groq_key/" .env
            fi
            
            if [ ! -z "$openai_key" ]; then
                sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
            fi
            
            if [ ! -z "$anthropic_key" ]; then
                sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$anthropic_key/" .env
            fi
            
            print_success "Clés API configurées avec succès."
        fi
    else
        print_message "Fichier .env existant détecté."
    fi
    
    print_success "Environnement configuré avec succès."
}

# Construire et démarrer les conteneurs
build_and_start() {
    print_message "Construction et démarrage des conteneurs..."
    
    # Arrêter les conteneurs existants
    docker-compose down
    
    # Construire les images
    docker-compose build
    
    # Démarrer les conteneurs
    docker-compose up -d
    
    print_success "Conteneurs démarrés avec succès."
}

# Initialiser la base de données vectorielle
init_vector_db() {
    print_message "Initialisation de la base de données vectorielle..."
    
    # Attendre que Qdrant soit prêt
    print_message "Attente du démarrage de Qdrant..."
    until docker-compose exec -T qdrant curl -s -f "http://localhost:6333/health" > /dev/null; do
        echo -n "."
        sleep 5
    done
    echo ""
    
    # Exécuter le script d'initialisation
    docker-compose exec -T api bash -c "cd /app && python -m scripts.seed_vector_db"
    
    print_success "Base de données vectorielle initialisée avec succès."
}

# Vérifier que tous les services sont opérationnels
check_services() {
    print_message "Vérification des services..."
    
    # Vérifier l'API
    if curl -s -f "http://localhost/api/health" > /dev/null; then
        print_success "API opérationnelle."
    else
        print_error "L'API n'est pas accessible. Vérifiez les logs avec: docker-compose logs api"
    fi
    
    # Vérifier le frontend
    if curl -s -f "http://localhost/" > /dev/null; then
        print_success "Frontend opérationnel."
    else
        print_error "Le frontend n'est pas accessible. Vérifiez les logs avec: docker-compose logs frontend"
    fi
    
    # Vérifier MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.runCommand({ping:1})" > /dev/null; then
        print_success "MongoDB opérationnel."
    else
        print_error "MongoDB n'est pas opérationnel. Vérifiez les logs avec: docker-compose logs mongodb"
    fi
    
    # Vérifier Redis
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis opérationnel."
    else
        print_error "Redis n'est pas opérationnel. Vérifiez les logs avec: docker-compose logs redis"
    fi
    
    # Vérifier Qdrant
    if docker-compose exec -T qdrant curl -s -f "http://localhost:6333/health" > /dev/null; then
        print_success "Qdrant opérationnel."
    else
        print_error "Qdrant n'est pas opérationnel. Vérifiez les logs avec: docker-compose logs qdrant"
    fi
    
    print_message "Vérification des services terminée."
}

# Configurer HTTPS (optionnel)
setup_https() {
    print_message "Configuration HTTPS..."
    
    read -p "Souhaitez-vous configurer HTTPS avec Let's Encrypt? (o/n): " setup_https
    
    if [[ $setup_https == "o" || $setup_https == "O" ]]; then
        read -p "Entrez votre nom de domaine (ex: example.com): " domain_name
        
        # Installer certbot
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
        
        # Obtenir le certificat
        sudo certbot --nginx -d $domain_name
        
        # Mettre à jour la configuration Nginx
        cat > ./nginx/nginx.conf << EOF
server {
    listen 80;
    server_name $domain_name;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $domain_name;

    ssl_certificate /etc/letsencrypt/live/$domain_name/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain_name/privkey.pem;
    
    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Support pour les requêtes WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts plus longs pour les opérations d'analyse
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Uploads
    location /uploads/ {
        proxy_pass http://api:8000/uploads/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        client_max_body_size 10M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
EOF
        
        # Redémarrer Nginx
        docker-compose restart nginx
        
        print_success "HTTPS configuré avec succès pour $domain_name."
    else
        print_message "Configuration HTTPS ignorée."
    fi
}

# Configurer les sauvegardes (optionnel)
setup_backups() {
    print_message "Configuration des sauvegardes..."
    
    read -p "Souhaitez-vous configurer des sauvegardes automatiques? (o/n): " setup_backups
    
    if [[ $setup_backups == "o" || $setup_backups == "O" ]]; then
        read -p "Entrez le chemin pour stocker les sauvegardes (ex: /path/to/backups): " backup_path
        
        # Créer le répertoire de sauvegarde
        mkdir -p $backup_path
        
        # Créer le script de sauvegarde
        cat > ./scripts/backup.sh << EOF
#!/bin/bash

# Script de sauvegarde pour le PoC d'analyse de documents juridiques
BACKUP_PATH=$backup_path
DATE=\$(date +%Y-%m-%d)

# Sauvegarde MongoDB
docker-compose exec -T mongodb mongodump --out /dump
docker cp \$(docker-compose ps -q mongodb):/dump \$BACKUP_PATH/mongodb-\$DATE

# Sauvegarde des documents
docker cp \$(docker-compose ps -q api):/app/uploads \$BACKUP_PATH/uploads-\$DATE

# Sauvegarde de Qdrant
docker cp \$(docker-compose ps -q qdrant):/qdrant/storage \$BACKUP_PATH/qdrant-\$DATE

# Compression des sauvegardes
cd \$BACKUP_PATH
tar -czf backup-\$DATE.tar.gz mongodb-\$DATE uploads-\$DATE qdrant-\$DATE
rm -rf mongodb-\$DATE uploads-\$DATE qdrant-\$DATE

echo "Sauvegarde terminée: \$BACKUP_PATH/backup-\$DATE.tar.gz"
EOF
        
        # Rendre le script exécutable
        chmod +x ./scripts/backup.sh
        
        # Ajouter la tâche cron
        (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup.sh") | crontab -
        
        print_success "Sauvegardes configurées avec succès. Une sauvegarde sera effectuée chaque jour à 2h du matin."
    else
        print_message "Configuration des sauvegardes ignorée."
    fi
}

# Afficher les informations de déploiement
show_deployment_info() {
    print_message "Informations de déploiement:"
    echo ""
    echo "Application déployée avec succès!"
    echo ""
    echo "URLs d'accès:"
    echo "- Frontend: http://localhost"
    echo "- API: http://localhost/api"
    echo "- Documentation API: http://localhost/api/docs"
    echo ""
    echo "Commandes utiles:"
    echo "- Voir les logs: docker-compose logs -f"
    echo "- Redémarrer les services: docker-compose restart"
    echo "- Arrêter l'application: docker-compose down"
    echo ""
    echo "Pour plus d'informations, consultez la documentation:"
    echo "- README.md: Documentation générale"
    echo "- docs/installation.md: Guide d'installation et de déploiement"
    echo "- docs/architecture.md: Architecture technique et workflows"
    echo "- docs/fonctionnalites.md: Guide d'utilisation des fonctionnalités"
    echo ""
}

# Fonction principale
main() {
    echo "=== Déploiement automatisé du PoC d'analyse de documents juridiques ==="
    echo ""
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Configurer l'environnement
    setup_environment
    
    # Construire et démarrer les conteneurs
    build_and_start
    
    # Initialiser la base de données vectorielle
    init_vector_db
    
    # Vérifier que tous les services sont opérationnels
    check_services
    
    # Configurer HTTPS (optionnel)
    setup_https
    
    # Configurer les sauvegardes (optionnel)
    setup_backups
    
    # Afficher les informations de déploiement
    show_deployment_info
    
    echo "=== Déploiement terminé avec succès ! ==="
}

# Exécuter la fonction principale
main

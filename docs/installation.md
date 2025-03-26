# Guide d'installation et de déploiement

Ce document fournit les instructions détaillées pour installer et déployer le PoC d'analyse de documents juridiques.

## Installation en environnement de développement

### Prérequis

- Docker et Docker Compose
- Git
- Clés API pour les modèles de langage (au moins une parmi Groq, OpenAI ou Anthropic)

### Étapes d'installation

1. **Cloner le dépôt**

```bash
git clone https://github.com/votre-utilisateur/legal-document-analyzer.git
cd legal-document-analyzer
```

2. **Configurer les variables d'environnement**

```bash
cp .env.example .env
```

Éditez le fichier `.env` pour configurer les variables suivantes :

```
# Clés API pour les modèles de langage
GROQ_API_KEY=votre_clé_groq
OPENAI_API_KEY=votre_clé_openai
ANTHROPIC_API_KEY=votre_clé_anthropic

# Fournisseur LLM par défaut (groq, openai, anthropic)
LLM_PROVIDER=groq

# Informations d'authentification MongoDB
MONGODB_USER=admin
MONGODB_PASSWORD=password_securise

# Mot de passe Redis
REDIS_PASSWORD=password_securise
```

3. **Vérifier l'environnement**

Exécutez le script de vérification pour vous assurer que tous les fichiers nécessaires sont présents :

```bash
chmod +x scripts/test_setup.sh
./scripts/test_setup.sh
```

4. **Démarrer les services**

```bash
docker-compose up -d
```

5. **Vérifier le déploiement**

```bash
./scripts/test_deployment.sh
```

L'application sera accessible à l'adresse : http://localhost

## Déploiement en production

Pour un déploiement en production, suivez ces étapes supplémentaires :

### 1. Sécuriser les variables d'environnement

- Utilisez un gestionnaire de secrets comme Docker Secrets ou HashiCorp Vault
- Ne stockez jamais les clés API directement dans les fichiers de configuration

### 2. Configurer HTTPS

1. Obtenez un certificat SSL (Let's Encrypt est recommandé)
2. Modifiez la configuration Nginx pour utiliser HTTPS :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name votre-domaine.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # Reste de la configuration...
}
```

### 3. Configurer les volumes persistants

Modifiez le fichier `docker-compose.yml` pour utiliser des volumes nommés ou des volumes hôtes pour les données persistantes :

```yaml
volumes:
  mongodb_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/persistent/mongodb
      o: bind
  qdrant_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/persistent/qdrant
      o: bind
  redis_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/persistent/redis
      o: bind
  uploaded_documents:
    driver: local
    driver_opts:
      type: none
      device: /path/to/persistent/uploads
      o: bind
```

### 4. Configurer les sauvegardes

Créez un script de sauvegarde pour MongoDB et les documents téléchargés :

```bash
#!/bin/bash
# Sauvegarde MongoDB
docker exec legal-analyzer-mongodb mongodump --out /backup/$(date +%Y-%m-%d)
# Sauvegarde des documents
cp -r /path/to/persistent/uploads /backup/uploads-$(date +%Y-%m-%d)
```

Ajoutez ce script à cron pour des sauvegardes régulières :

```
0 2 * * * /path/to/backup.sh
```

### 5. Configurer le monitoring

Ajoutez Prometheus et Grafana pour surveiller les performances et la santé du système :

```yaml
# Ajouter à docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus:/etc/prometheus
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  volumes:
    - grafana_data:/var/lib/grafana
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
```

### 6. Optimiser les performances

Pour les déploiements à grande échelle :

1. Utilisez un équilibreur de charge comme HAProxy ou Nginx Plus
2. Déployez plusieurs instances de l'API FastAPI
3. Configurez MongoDB en mode répliqué
4. Utilisez Redis pour la mise en cache des résultats fréquemment demandés

## Mise à jour du système

Pour mettre à jour le système vers une nouvelle version :

1. Arrêtez les conteneurs :
```bash
docker-compose down
```

2. Tirez les dernières modifications :
```bash
git pull origin main
```

3. Reconstruisez les images :
```bash
docker-compose build
```

4. Redémarrez les conteneurs :
```bash
docker-compose up -d
```

## Dépannage

### Problèmes courants et solutions

1. **Les conteneurs ne démarrent pas**
   - Vérifiez les logs : `docker-compose logs`
   - Assurez-vous que les ports ne sont pas déjà utilisés

2. **L'API n'est pas accessible**
   - Vérifiez que le conteneur API est en cours d'exécution : `docker-compose ps`
   - Vérifiez les logs de l'API : `docker-compose logs api`

3. **Erreurs de connexion à MongoDB**
   - Vérifiez que MongoDB est en cours d'exécution : `docker-compose ps mongodb`
   - Vérifiez les variables d'environnement dans le fichier `.env`

4. **Erreurs d'appel aux LLM**
   - Vérifiez que les clés API sont correctement configurées
   - Vérifiez la connectivité Internet depuis les conteneurs

5. **Problèmes de performance**
   - Augmentez les ressources allouées à Docker
   - Vérifiez l'utilisation des ressources : `docker stats`

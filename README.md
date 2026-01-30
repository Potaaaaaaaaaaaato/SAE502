# SAE502 - Déploiement automatisé Django

![SAE502 Banner](https://img.shields.io/badge/SAE502-Automatisation%20Django-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

## Description

Projet SAE502 : **Automatisation complète du déploiement, de la sécurisation et de la supervision d'un site web Django en production** par conteneurisation Docker et Ansible.

Ce projet supprime totalement les interventions manuelles de déploiement grâce à :
- **Conteneurisation complète** avec Docker Compose
- **Automatisation du déploiement** avec Ansible
- **Sécurisation** avec HTTPS, fail2ban, UFW
- **Monitoring proactif** avec alertes
- **Backups automatiques** quotidiens
- **CI/CD** avec GitHub Actions

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS (443) / HTTP (80)
                        ▼
                ┌───────────────┐
                │  Nginx        │  Reverse Proxy
                │  Container    │  + SSL/TLS
                └───────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────┐   ┌──────────────┐  ┌──────────┐
│  Django   │   │ PostgreSQL   │  │  Redis   │
│  Gunicorn │◄──┤  Database    │  │  Cache   │
└───────────┘   └──────────────┘  └──────────┘
        ▲
        │
┌───────────────┐
│  Monitoring   │  Health Checks
│  Container    │  + Alerts
└───────────────┘
```

### Services conteneurisés

| Service | Description | Port | Volume |
|---------|-------------|------|--------|
| **django-app** | Application Django + Gunicorn | 8000 (interne) | static, media, logs |
| **nginx** | Reverse proxy, HTTPS, fichiers statiques | 80, 443 | static, media, ssl |
| **postgresql** | Base de données relationnelle | 5432 (interne) | postgres_data |
| **redis** | Cache et broker Celery | 6379 (interne) | redis_data |
| **monitoring** | Healthchecks et alertes | - | - |

## Démarrage rapide

### Prérequis

- Docker 24.0+
- Docker Compose 2.20+
- Git

### Installation locale (développement)

1. **Cloner le repository**
   ```bash
   git clone <votre-repo>
   cd SAE502
   ```

2. **Configurer les variables d'environnement**
   ```bash
   cd docker
   cp .env.local .env
   # Optionnel : modifier les variables dans .env
   ```

3. **Lancer les conteneurs**
   ```bash
   docker compose up -d --build
   ```

4. **Vérifier que tout fonctionne**
   ```bash
   # Voir le statut des conteneurs
   docker compose ps
   
   # Voir les logs
   docker compose logs -f
   
   # Accéder à l'application
   open http://localhost
   ```

5. **Accéder aux différentes pages**
   - Page d'accueil : http://localhost
   - Démonstration : http://localhost/demo/
   - Healthcheck : http://localhost/health/
   - Admin Django : http://localhost/admin/ (admin/admin123)

## Structure du projet

```
SAE502/
├── app/                          # Application Django
│   └── SAE502/
│       ├── SAE/                  # Application de démonstration
│       │   ├── templates/        # Templates HTML
│       │   ├── views.py          # Vues Django
│       │   └── urls.py           # Routes
│       ├── SAE502/               # Configuration Django
│       │   ├── settings.py       # Configuration production
│       │   └── urls.py           # URLs principales
│       └── requirements.txt      # Dépendances Python
│
├── docker/                       # Configuration Docker
│   ├── docker-compose.yml        # Orchestration des services
│   ├── .env.local                # Variables d'environnement (dev)
│   ├── django/
│   │   ├── Dockerfile            # Image Django
│   │   └── entrypoint.sh         # Script de démarrage
│   ├── nginx/
│   │   ├── Dockerfile            # Image Nginx
│   │   ├── nginx.conf            # Configuration Nginx
│   │   └── ssl/                  # Certificats SSL
│   └── monitoring/
│       ├── Dockerfile            # Image monitoring
│       └── healthcheck.py        # Script de healthcheck
│
├── ansible/                      # Playbooks Ansible
│   ├── site.yml                  # Playbook master
│   ├── ansible.cfg               # Configuration Ansible
│   ├── setup-multipass-ssh.sh    # Script de configuration SSH Multipass
│   ├── playbooks/                # Playbooks modulaires
│   │   ├── 01-prepare-host.yml
│   │   ├── 02-install-docker.yml
│   │   ├── 03-deploy-application.yml
│   │   ├── 04-ssl-letsencrypt.yml
│   │   ├── 04-ssl-letsencrypt-conditional.yml
│   │   ├── 05-security-hardening.yml
│   │   ├── 06-monitoring-alerting.yml
│   │   └── 07-backup-database.yml
│   ├── inventories/
│   │   ├── production/
│   │   │   └── hosts
│   │   └── multipass/            # Inventaire de test Multipass
│   │       ├── hosts
│   │       └── group_vars/all.yml
│   ├── group_vars/
│   │   └── all.yml               # Variables globales
│   └── templates/                # Templates Jinja2
│
├── scripts/                      # Scripts utilitaires
│   ├── backup.sh
│   ├── restore.sh
│   ├── deploy.sh
│   └── rollback.sh
│
├── docs/                         # Documentation Sphinx
│   └── (à générer)
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # Pipeline CI/CD
│
├── .env.example                  # Template variables production
└── README.md                     # Ce fichier
```

## Configuration

### Variables d'environnement

Le fichier `.env` contient toutes les variables de configuration. Copiez `.env.example` et adaptez :

```bash
# Django
DEBUG=False
DJANGO_SECRET_KEY=votre-cle-secrete-tres-longue
ALLOWED_HOSTS=localhost,yourdomain.com

# Base de données
DB_NAME=django_db
DB_USER=djangouser
DB_PASSWORD=mot-de-passe-securise

# Email (pour alertes)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-specific-password
ALERT_EMAIL=admin@yourdomain.com

# Monitoring
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

## Production avec ansible

### Deploiement complet sur serveur vierge

1. **Configurer l'inventaire Ansible**
   ```bash
   vi ansible/inventories/production/hosts
   # Ajouter votre serveur
   ```

2. **Configurer Ansible Vault pour les secrets**
   ```bash
   ansible-vault create ansible/group_vars/production/vault.yml
   # Ajouter vos secrets
   ```

3. **Lancer le deploiement complet**
   ```bash
   ansible-playbook -i ansible/inventories/production ansible/site.yml --ask-vault-pass
   ```

### Test local avec Multipass (macOS/Linux)

```bash
# Creer la VM
multipass launch --name sae502-test -c 2 -m 2G -d 20G

# Configurer SSH
cd ansible
./setup-multipass-ssh.sh

# Deploiement complet
ansible-playbook -i inventories/multipass/hosts \
  playbooks/01-prepare-host.yml \
  playbooks/02-install-docker.yml \
  playbooks/03-deploy-application.yml \
  playbooks/04-ssl-letsencrypt-conditional.yml \
  playbooks/05-security-hardening.yml \
  playbooks/06-monitoring-alerting.yml \
  playbooks/07-backup-database.yml

# Stopper la VM
multipass stop sae502-test
```

En **une seule commande**, les playbooks vont :
- Préparer le serveur (Docker, dépendances, utilisateur)
- Configurer le firewall (UFW) et fail2ban
- Déployer l'application avec Docker Compose
- Générer les certificats SSL Let's Encrypt
- Configurer le monitoring et les alertes
- Configurer les backups automatiques
- Générer la documentation

## Monitoring et healthcheck

Le conteneur `monitoring` vérifie périodiquement :
- Disponibilité de Django
- Connexion à PostgreSQL
- Connexion à Redis
- Espace disque disponible

En cas de problème, des alertes sont envoyées par :
- Email
- Webhook (Slack/Discord)

### Endpoint healthcheck

```bash
curl http://localhost/health/
```

Retourne :
```json
{
  "django": "OK",
  "database": "OK",
  "redis": "OK",
  "disk": {"usage_percent": 45, "healthy": true},
  "status": "healthy",
  "timestamp": "2025-12-09T08:30:00"
}
```

## Sécurité

### Mesures implémentées

- **HTTPS obligatoire** avec certificats Let's Encrypt
- **Headers de sécurité** (HSTS, X-Frame-Options, CSP)
- **Isolation réseau** Docker (seul Nginx exposé)
- **Utilisateur non-root** dans les conteneurs
- **Firewall UFW** (ports 22, 80, 443 uniquement)
- **fail2ban** contre brute-force
- **Secrets chiffrés** avec Ansible Vault
- **Connexion SSH** par clés uniquement (root désactivé)

## Backups

Les backups automatiques de PostgreSQL sont configurés via Ansible :
- **Fréquence** : Quotidien à 2h du matin
- **Rotation** : 7 jours
- **Format** : pg_dump compressé (gzip)

### Backup Manuel

```bash
./scripts/backup.sh
```

### Restauration

```bash
./scripts/restore.sh /path/to/backup.sql.gz
```

## CI/CD

Intégration complète avec GitHub Actions pour automatiser tests, builds et déploiement.

### Workflows disponibles

#### 🧪 CI - Continuous Integration
**Déclenchement** : Push sur `main`/`develop`, Pull Requests  
**Actions** :
- ✅ Linting (Black, isort, flake8)
- ✅ Tests Django avec PostgreSQL et Redis
- ✅ Build et validation des images Docker
- ✅ Scan de sécurité (Trivy)

#### 🐳 Build & Push Docker Images
**Déclenchement** : Push sur `main`, tags, manuel  
**Actions** :
- 📦 Build des 3 images (django-app, nginx, monitoring)
- 📤 Push vers GitHub Container Registry (GHCR)
- 🏷️ Tagging automatique (latest, version, sha)
- 🔔 Notifications Slack/Telegram

#### 🚀 CD - Continuous Deployment (manuel - exemple)
**Déclenchement** : Manuel uniquement  
**Actions** :
- 🎯 Choix de l'environnement (staging/production)
- 📋 Sélection du tag d'image à déployer
- 🤖 Déploiement via Ansible
- ✅ Health check post-déploiement
- 🔔 Notifications de succès/échec

### Configuration (exemple)

Voir [.github/CICD_GUIDE.md](.github/CICD_GUIDE.md) pour :
- Configuration des secrets GitHub
- Setup des notifications (Slack/Telegram)
- Instructions de déploiement
- Troubleshooting

## Documentation (exemple)

La documentation complète est générée automatiquement avec Sphinx et accessible à `/docs` :

```bash
# Générer la documentation localement
cd docs
sphinx-build -b html . _build/html
```

---

## Objectifs du projet

Ce projet répond aux objectifs suivants :
- Déploiement 100 % automatisé et reproductible
- Sécurité de l'environnement de production garantie
- Supervision proactive avec alertes
- Chaîne CI/CD complète
- Documentation technique générée automatiquement

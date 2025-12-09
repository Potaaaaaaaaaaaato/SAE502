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
│   ├── playbook-prepare-host.yml
│   ├── playbook-deploy-application.yml
│   ├── playbook-ssl-letsencrypt.yml
│   ├── playbook-security-hardening.yml
│   ├── playbook-monitoring-alerting.yml
│   ├── playbook-backup-database.yml
│   ├── playbook-rollback.yml
│   ├── playbook-cleanup.yml
│   └── inventories/
│       └── production/
│           └── hosts
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

### Déploiement complet sur serveur vierge

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

3. **Lancer le déploiement complet**
   ```bash
   ansible-playbook -i ansible/inventories/production ansible/site.yml --ask-vault-pass
   ```

En **une seule commande**, le playbook maître va :
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

Le pipeline GitHub Actions s'exécute automatiquement sur chaque push vers `main` :

1. **Tests** : Linting (flake8), tests unitaires Django
2. **Build** : Construction des images Docker
3. **Deploy** : Déploiement automatique via Ansible

## Documentation

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
# SAE502 - Documentation Complète du Projet

> **Contexte pour Claude AI** : Ce fichier contient toutes les informations nécessaires pour comprendre, modifier et étendre ce projet.

---

## 📋 Résumé du Projet

**SAE502** est un projet de déploiement automatisé d'une application web Django en production. L'objectif est de supprimer totalement les interventions manuelles de déploiement grâce à :

- **Conteneurisation complète** avec Docker Compose
- **Automatisation du déploiement** avec Ansible
- **Sécurisation** avec HTTPS (Let's Encrypt), fail2ban, UFW
- **Monitoring proactif** avec alertes email/webhook
- **Backups automatiques** de la base de données PostgreSQL
- **CI/CD** avec GitHub Actions (prévu)

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS (443) / HTTP (80)
                        ▼
                ┌───────────────┐
                │     Nginx     │  Reverse Proxy + SSL/TLS
                │   Container   │  Fichiers statiques
                └───────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────┐   ┌──────────────┐  ┌──────────┐
│  Django   │   │  PostgreSQL  │  │  Redis   │
│  Gunicorn │◄──┤   Database   │  │  Cache   │
│  (8000)   │   │   (5432)     │  │  (6379)  │
└───────────┘   └──────────────┘  └──────────┘
        ▲
        │
┌───────────────┐
│  Monitoring   │  Health Checks + Alertes
│   Container   │  (Email & Webhook)
└───────────────┘
```

### Services Docker

| Service | Image/Build | Port | Description |
|---------|-------------|------|-------------|
| `django-app` | Build custom | 8000 (interne) | Application Django + Gunicorn |
| `nginx` | Build custom | 80, 443 | Reverse proxy, SSL, fichiers statiques |
| `postgresql` | postgres:16-alpine | 5432 (interne) | Base de données |
| `redis` | redis:7-alpine | 6379 (interne) | Cache et sessions |
| `monitoring` | Build custom | - | Health checks et alertes |

---

## 📁 Structure du Projet

```
SAE502/
├── app/                              # Application Django
│   ├── requirements.txt              # Dépendances Python
│   ├── SAE/                          # App de démonstration
│   │   ├── templates/                # Templates HTML (base.html, home.html, demo.html)
│   │   ├── views.py                  # 3 vues : home, healthcheck, demo
│   │   ├── urls.py                   # Routes de l'app
│   │   ├── models.py                 # Modèles (vide actuellement)
│   │   ├── admin.py                  # Config admin
│   │   └── tests.py                  # Tests unitaires
│   └── SAE502/
│       └── SAE502/                   # Configuration Django
│           ├── settings.py           # Settings production-ready
│           ├── urls.py               # URLs principales
│           ├── wsgi.py               # Point d'entrée WSGI
│           └── __init__.py
│
├── docker/                           # Configuration Docker
│   ├── docker-compose.yml            # Orchestration (5 services)
│   ├── .env                          # Variables d'environnement locales
│   ├── QUICKSTART.md                 # Guide de démarrage rapide
│   ├── django/
│   │   ├── Dockerfile                # Multi-stage build, Python 3.11-slim
│   │   └── entrypoint.sh             # Script de démarrage (migrations, etc.)
│   ├── nginx/
│   │   ├── Dockerfile                # Image Nginx personnalisée
│   │   └── nginx.conf                # Configuration HTTP (dev local)
│   └── monitoring/
│       ├── Dockerfile                # Image monitoring
│       └── healthcheck.py            # Script Python complet (296 lignes)
│
├── ansible/                          # Automatisation Ansible
│   ├── site.yml                      # Playbook maître (orchestre tout)
│   ├── ansible.cfg                   # Configuration Ansible
│   ├── Vagrantfile                   # Pour tests locaux avec Vagrant
│   ├── TEST_VAGRANT.md               # Guide de test Vagrant
│   ├── TEST_MULTIPASS.md             # Guide de test Multipass
│   ├── group_vars/
│   │   └── all.yml                   # Variables globales (projet, déploiement, sécurité)
│   ├── inventories/                  # Inventaires par environnement
│   ├── templates/                    # Templates Jinja2 pour config
│   └── playbooks/                    # 8 playbooks modulaires
│       ├── 01-prepare-host.yml       # Préparation serveur Ubuntu/Debian
│       ├── 02-install-docker.yml     # Installation Docker + Compose
│       ├── 03-deploy-application.yml # Déploiement de l'application
│       ├── 04-ssl-letsencrypt.yml    # Certificats SSL Let's Encrypt
│       ├── 05-security-hardening.yml # UFW + fail2ban + sysctl
│       ├── 06-monitoring-alerting.yml# Configuration monitoring
│       └── 07-backup-database.yml    # Configuration backups automatiques
│
├── scripts/                          # Scripts utilitaires (bash)
│   ├── backup.sh                     # Backup manuel
│   ├── restore.sh                    # Restauration backup
│   ├── deploy.sh                     # Déploiement manuel
│   └── rollback.sh                   # Rollback version précédente
│
├── docs/                             # Documentation Sphinx (à générer)
├── .github/                          # GitHub Actions (CI/CD à implémenter)
├── .env.example                      # Template variables production
├── .gitignore                        # Fichiers ignorés Git
└── README.md                         # Documentation principale
```

---

## ⚙️ Stack Technique

### Backend
- **Django 4.2.8** - Framework web Python
- **Gunicorn 21.2.0** - Serveur WSGI de production
- **PostgreSQL 16** - Base de données relationnelle
- **Redis 7** - Cache et broker de tâches
- **Celery 5.3.4** - File de tâches asynchrones (installé, pas encore utilisé)

### Frontend
- **HTML5/CSS3** - Templates Django responsive
- **Google Fonts (Outfit)** - Typographie moderne

### Infrastructure
- **Docker & Docker Compose 3.8** - Conteneurisation
- **Nginx** - Reverse proxy et fichiers statiques
- **Let's Encrypt** - Certificats SSL/TLS gratuits

### Automatisation
- **Ansible** - Déploiement et configuration serveur
- **Ansible Vault** - Chiffrement des secrets
- **UFW** - Firewall Ubuntu
- **fail2ban** - Protection anti-brute-force

### Monitoring
- **Script Python custom** (`healthcheck.py`) - Checks Django, PostgreSQL, Redis, disk
- **Alertes email** via SMTP
- **Alertes webhook** (Slack/Discord compatible)

---

## 🔧 Configuration Django (settings.py)

Le fichier `app/SAE502/SAE502/settings.py` est configuré pour la production :

### Variables d'environnement utilisées
```python
# Sécurité
DJANGO_SECRET_KEY          # Clé secrète (obligatoire en prod)
DEBUG                      # False en production
ALLOWED_HOSTS              # Domaines autorisés

# Base de données PostgreSQL
DB_ENGINE                  # django.db.backends.postgresql
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Cache Redis
REDIS_URL                  # redis://redis:6379/0

# Email
EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS
EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL

# Sécurité HTTPS
SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
HSTS_SECONDS               # 31536000 (1 an)
```

### Applications installées
- `django.contrib.admin` - Interface d'administration
- `django.contrib.auth` - Authentification
- `SAE` - Application de démonstration

### Fonctionnalités
- Sessions stockées dans Redis
- Logging vers console et fichier rotatif
- Fuseau horaire : Europe/Paris
- Langue : Français

---

## 🌐 Routes de l'Application

| Route | Vue | Description |
|-------|-----|-------------|
| `/` | `home` | Page d'accueil avec présentation du projet |
| `/health/` | `healthcheck` | Endpoint JSON pour monitoring |
| `/demo/` | `demo` | Page démo avec compteur de visites (Redis) |
| `/admin/` | Admin Django | Interface d'administration |
| `/static/` | Nginx | Fichiers statiques |
| `/media/` | Nginx | Fichiers uploadés |
| `/docs/` | Nginx | Documentation Sphinx |

### Endpoint Healthcheck

```bash
curl http://localhost/health/
```

Réponse :
```json
{
  "django": "OK",
  "database": "OK|ERROR: ...",
  "redis": "OK|ERROR: ...",
  "timestamp": "2025-12-14T16:00:00+01:00",
  "status": "healthy|unhealthy"
}
```

---

## 🐳 Docker Compose

### Démarrage local

```bash
cd docker
cp .env.local .env  # ou modifier les variables dans .env
docker compose up -d --build
```

### Commandes utiles

```bash
# État des conteneurs
docker compose ps

# Logs en temps réel
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f django-app

# Reconstruire un service
docker compose up -d --build django-app

# Exécuter une commande Django
docker compose exec django-app python manage.py shell

# Créer un superuser
docker compose exec django-app python manage.py createsuperuser

# Arrêter tout
docker compose down

# Arrêter et supprimer les volumes
docker compose down -v
```

### Volumes Docker

| Volume | Chemin conteneur | Description |
|--------|------------------|-------------|
| `postgres_data` | `/var/lib/postgresql/data` | Données PostgreSQL |
| `redis_data` | `/data` | Données Redis |
| `static_volume` | `/app/staticfiles` | Fichiers statiques Django |
| `media_volume` | `/app/mediafiles` | Uploads utilisateurs |
| `docs_volume` | `/app/docs` | Documentation générée |

---

## 🔐 Sécurité

### Mesures implémentées

1. **HTTPS** - Redirection automatique HTTP → HTTPS
2. **Headers de sécurité** - HSTS, X-Frame-Options, CSP, X-Content-Type-Options
3. **Isolation réseau** - Seul Nginx est exposé publiquement
4. **Utilisateur non-root** - Conteneur Django tourne avec user `django`
5. **Firewall UFW** - Ports ouverts : 22 (SSH), 80 (HTTP), 443 (HTTPS)
6. **fail2ban** - Protection contre brute-force SSH et Nginx
7. **Secrets chiffrés** - Ansible Vault pour les mots de passe
8. **SSH sécurisé** - Clés uniquement, root désactivé

### Variables Vault Ansible (à créer)

```yaml
# ansible/group_vars/production/vault.yml
vault_django_secret_key: "..."
vault_django_superuser_username: "admin"
vault_django_superuser_password: "..."
vault_django_superuser_email: "admin@example.com"
vault_db_password: "..."
vault_smtp_username: "..."
vault_smtp_password: "..."
vault_alert_email: "..."
vault_webhook_url: "..."
```

---

## 🚀 Déploiement avec Ansible

### Pipeline de déploiement (site.yml)

Le playbook maître `ansible/site.yml` orchestre 7 phases :

1. **Phase 1** - Préparation serveur (packages, user deploy, SSH)
2. **Phase 2** - Installation Docker + Docker Compose
3. **Phase 3** - Déploiement application (git clone, docker compose up)
4. **Phase 4** - Configuration SSL Let's Encrypt
5. **Phase 5** - Hardening sécurité (UFW, fail2ban, sysctl)
6. **Phase 6** - Configuration monitoring et alertes
7. **Phase 7** - Configuration backups automatiques
8. **Validation finale** - Tests HTTPS et résumé

### Commande de déploiement

```bash
# Déploiement complet sur production
ansible-playbook -i ansible/inventories/production ansible/site.yml --ask-vault-pass

# Déploiement d'un playbook spécifique
ansible-playbook -i ansible/inventories/production ansible/playbooks/03-deploy-application.yml
```

### Variables globales (group_vars/all.yml)

```yaml
project_name: sae502
project_root: /opt/sae502
deploy_user: deploy
domain_name: yourdomain.com
backup_retention_days: 7
backup_time: "2:00"
monitoring_check_interval: 300  # 5 minutes
```

### Test local avec Vagrant

```bash
cd ansible
vagrant up
ansible-playbook -i inventories/vagrant site.yml
```

---

## 📊 Monitoring

### Script healthcheck.py

Le conteneur `monitoring` exécute périodiquement des vérifications :

- ✅ **Django** - HTTP GET sur `/health/`
- ✅ **PostgreSQL** - Connexion et requête `SELECT 1`
- ✅ **Redis** - Commande `PING`
- ✅ **Espace disque** - Alerte si > 90%

### Alertes

En cas d'échec, envoi automatique :
- **Email** via SMTP (Gmail compatible)
- **Webhook** format Slack/Discord

---

## 💾 Backups

### Configuration

- **Fréquence** : Quotidien à 2h du matin (cron)
- **Rétention** : 7 jours
- **Format** : `pg_dump` compressé (gzip)
- **Emplacement** : `/opt/sae502/backups/`

### Commandes manuelles

```bash
# Backup manuel
./scripts/backup.sh

# Restauration
./scripts/restore.sh /path/to/backup.sql.gz
```

---

## 📝 Conventions de Code

### Python/Django
- PEP 8 pour le style
- Docstrings pour toutes les fonctions publiques
- Type hints recommandés
- Tests unitaires dans `tests.py`

### Ansible
- Un playbook par fonctionnalité
- Variables dans `group_vars/`
- Secrets dans Ansible Vault
- Tags pour filtrer les tâches

### Docker
- Multi-stage builds pour images optimisées
- `.dockerignore` pour exclure fichiers inutiles
- Healthchecks dans chaque service

---

## 🧪 Tests

### Tests Django

```bash
# Dans le conteneur
docker compose exec django-app python manage.py test

# Localement (avec venv)
cd app
python manage.py test
```

### Tests Ansible (syntaxe)

```bash
ansible-playbook --syntax-check ansible/site.yml
```

### Test de l'application

```bash
# Page d'accueil
curl http://localhost/

# Healthcheck
curl http://localhost/health/

# Page démo
curl http://localhost/demo/
```

---

## 🔄 Workflow de Développement

1. **Modifier le code** dans `app/`
2. **Reconstruire** : `docker compose up -d --build django-app`
3. **Vérifier les logs** : `docker compose logs -f django-app`
4. **Tester** : Naviguer vers http://localhost/

### Hot-reload (développement)

Pour activer le rechargement automatique, modifier le `docker-compose.yml` pour monter le code source :

```yaml
django-app:
  volumes:
    - ../app:/app:ro  # Ajouter cette ligne
```

---

## 🐛 Dépannage

### Conteneur ne démarre pas

```bash
docker compose logs django-app
# Vérifier les erreurs de migration, connexion DB, etc.
```

### Base de données inaccessible

```bash
# Vérifier que PostgreSQL est prêt
docker compose exec postgresql pg_isready -U user -d django_db
```

### Redis inaccessible

```bash
# Test de connexion Redis
docker compose exec redis redis-cli ping
# Doit retourner "PONG"
```

### Fichiers statiques manquants

```bash
# Collecter les fichiers statiques
docker compose exec django-app python manage.py collectstatic --noinput
```

---

## 📚 Ressources

- [Documentation Django](https://docs.djangoproject.com/fr/4.2/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Ansible Documentation](https://docs.ansible.com/)
- [Let's Encrypt](https://letsencrypt.org/docs/)
- [fail2ban](https://www.fail2ban.org/)

---

## 👤 Informations Projet

- **Projet** : SAE502 - 3ème année
- **Objectif** : Automatisation complète du déploiement d'une application web
- **Technologies clés** : Django, Docker, Ansible, PostgreSQL, Redis, Nginx

---

*Dernière mise à jour : 14 décembre 2025*

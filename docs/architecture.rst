Architecture
============

Cette page décrit l'architecture complète du projet SAE502.

Vue d'ensemble
--------------

Le projet SAE502 utilise une architecture microservices conteneurisée avec Docker Compose.
Tous les services sont isolés dans des conteneurs Docker et communiquent via un réseau privé.

Diagramme d'architecture
-------------------------

.. code-block:: text

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

Services conteneurisés
----------------------

Le projet est composé de 5 services principaux :

1. django-app
~~~~~~~~~~~~~

**Description** : Application Django avec serveur Gunicorn

* **Port** : 8000 (interne uniquement)
* **Volumes** :
  
  * ``static/`` - Fichiers statiques (CSS, JS, images)
  * ``media/`` - Fichiers uploadés par les utilisateurs
  * ``logs/`` - Logs de l'application

* **Dépendances** : PostgreSQL, Redis
* **Healthcheck** : Endpoint ``/health/``

**Technologies** :

* Python 3.11
* Django 4.2
* Gunicorn (WSGI server)
* psycopg2 (PostgreSQL adapter)
* redis-py (Redis client)

2. nginx
~~~~~~~~

**Description** : Reverse proxy et serveur de fichiers statiques

* **Ports** : 
  
  * 80 (HTTP) - Redirige vers HTTPS
  * 443 (HTTPS) - Trafic sécurisé

* **Volumes** :
  
  * ``static/`` - Fichiers statiques Django
  * ``media/`` - Fichiers media Django
  * ``ssl/`` - Certificats SSL/TLS

* **Rôle** :
  
  * Reverse proxy vers Django (port 8000)
  * Servir les fichiers statiques directement
  * Terminaison SSL/TLS
  * Headers de sécurité (HSTS, CSP, etc.)

3. postgresql
~~~~~~~~~~~~~

**Description** : Base de données relationnelle

* **Port** : 5432 (interne uniquement)
* **Volume** : ``postgres_data/`` - Données persistantes
* **Version** : PostgreSQL 15
* **Backup** : Automatique quotidien via cron

**Configuration** :

* Encodage UTF-8
* Timezone UTC
* Connexions limitées aux conteneurs Docker

4. redis
~~~~~~~~

**Description** : Cache en mémoire et broker Celery

* **Port** : 6379 (interne uniquement)
* **Volume** : ``redis_data/`` - Persistance optionnelle
* **Version** : Redis 7
* **Utilisation** :
  
  * Cache de sessions Django
  * Cache de requêtes
  * Broker pour tâches asynchrones (Celery)

5. monitoring
~~~~~~~~~~~~~

**Description** : Service de healthcheck et alertes

* **Fonction** : Vérification périodique de la santé des services
* **Fréquence** : Toutes les 60 secondes
* **Alertes** : Email + Webhook (Slack/Discord)

**Vérifications** :

* Disponibilité de Django
* Connexion PostgreSQL
* Connexion Redis
* Espace disque disponible
* Charge CPU/Mémoire

Structure du projet
-------------------

.. code-block:: text

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
   │   ├── playbooks/                # Playbooks modulaires
   │   ├── inventories/              # Inventaires (prod, staging, etc.)
   │   └── templates/                # Templates Jinja2
   │
   ├── scripts/                      # Scripts utilitaires
   │   ├── backup.sh
   │   ├── restore.sh
   │   ├── deploy.sh
   │   └── rollback.sh
   │
   └── docs/                         # Documentation Sphinx

Réseau Docker
-------------

Tous les conteneurs communiquent via un réseau Docker privé nommé ``sae502_network``.

**Isolation** :

* Seul Nginx est exposé publiquement (ports 80, 443)
* Les autres services sont accessibles uniquement entre conteneurs
* Communication chiffrée en interne (optionnel)

**DNS interne** :

Les conteneurs peuvent se résoudre par leur nom de service :

* ``django-app`` → Application Django
* ``postgresql`` → Base de données
* ``redis`` → Cache
* ``nginx`` → Reverse proxy

Volumes et persistance
----------------------

Les données persistantes sont stockées dans des volumes Docker :

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Volume
     - Contenu
     - Backup
   * - ``postgres_data``
     - Base de données PostgreSQL
     - ✅ Quotidien
   * - ``static``
     - Fichiers statiques Django
     - ❌
   * - ``media``
     - Fichiers uploadés
     - ✅ Hebdomadaire
   * - ``redis_data``
     - Cache Redis (optionnel)
     - ❌
   * - ``logs``
     - Logs applicatifs
     - ✅ Rotation 7 jours

Flux de requêtes
----------------

1. **Requête HTTP/HTTPS** → Nginx (port 80/443)
2. **Nginx** vérifie :
   
   * Fichier statique ? → Servir directement
   * Fichier media ? → Servir directement
   * Autre ? → Proxy vers Django

3. **Django** (Gunicorn) traite la requête :
   
   * Consulte le cache Redis si nécessaire
   * Interroge PostgreSQL pour les données
   * Génère la réponse HTML/JSON

4. **Réponse** → Nginx → Client

Sécurité
--------

L'architecture intègre plusieurs couches de sécurité :

* **Isolation réseau** : Services non exposés publiquement
* **HTTPS obligatoire** : Certificats Let's Encrypt
* **Utilisateurs non-root** : Tous les conteneurs
* **Secrets** : Variables d'environnement (jamais en dur)
* **Firewall** : UFW sur l'hôte (ports 22, 80, 443 uniquement)
* **fail2ban** : Protection contre brute-force

Voir :doc:`security` pour plus de détails.

Scalabilité
-----------

L'architecture permet de scaler facilement :

**Horizontal** :

* Plusieurs instances Django derrière Nginx
* Load balancing avec Nginx
* PostgreSQL en réplication (master/slave)

**Vertical** :

* Augmentation des ressources CPU/RAM par conteneur
* Configuration dans ``docker-compose.yml``

Monitoring
----------

Le service de monitoring vérifie en continu :

* **Healthcheck Django** : ``/health/`` endpoint
* **PostgreSQL** : Connexion et requête test
* **Redis** : Ping
* **Disque** : Espace disponible < 90%
* **Mémoire** : Utilisation < 85%

Voir :doc:`monitoring` pour plus de détails.

Prochaines étapes
-----------------

* Consultez :doc:`docker` pour la configuration détaillée
* Déployez avec :doc:`ansible`
* Configurez le :doc:`monitoring`

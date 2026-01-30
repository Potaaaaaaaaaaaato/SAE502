Configuration Docker
====================

Cette page décrit la configuration Docker du projet SAE502.

Docker Compose
--------------

Le projet utilise Docker Compose pour orchestrer tous les services.

Fichier principal
~~~~~~~~~~~~~~~~~

Le fichier ``docker/docker-compose.yml`` définit tous les services :

.. code-block:: yaml

   version: '3.8'

   services:
     django-app:
       build: ./django
       volumes:
         - ../app:/app
         - static:/app/static
         - media:/app/media
       environment:
         - DEBUG=${DEBUG}
         - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
       depends_on:
         - postgresql
         - redis

     nginx:
       build: ./nginx
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - static:/static
         - media:/media
       depends_on:
         - django-app

     postgresql:
       image: postgres:15
       volumes:
         - postgres_data:/var/lib/postgresql/data
       environment:
         - POSTGRES_DB=${DB_NAME}
         - POSTGRES_USER=${DB_USER}
         - POSTGRES_PASSWORD=${DB_PASSWORD}

     redis:
       image: redis:7
       volumes:
         - redis_data:/data

     monitoring:
       build: ./monitoring
       depends_on:
         - django-app
         - postgresql
         - redis

   volumes:
     postgres_data:
     redis_data:
     static:
     media:

Variables d'environnement
--------------------------

Configuration via .env
~~~~~~~~~~~~~~~~~~~~~~

Le fichier ``.env`` contient toutes les variables de configuration :

.. code-block:: bash

   # Django
   DEBUG=False
   DJANGO_SECRET_KEY=votre-cle-secrete-tres-longue
   ALLOWED_HOSTS=localhost,yourdomain.com

   # Base de données
   DB_NAME=django_db
   DB_USER=djangouser
   DB_PASSWORD=mot-de-passe-securise
   DB_HOST=postgresql
   DB_PORT=5432

   # Redis
   REDIS_HOST=redis
   REDIS_PORT=6379

   # Email (pour alertes)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=app-specific-password
   ALERT_EMAIL=admin@yourdomain.com

   # Monitoring
   WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

Fichiers d'environnement
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``.env.local`` - Développement local
* ``.env.staging`` - Environnement de staging
* ``.env.production`` - Production (via Ansible Vault)

Images Docker
-------------

1. Django (django-app)
~~~~~~~~~~~~~~~~~~~~~~

**Dockerfile** : ``docker/django/Dockerfile``

.. code-block:: dockerfile

   FROM python:3.11-slim

   # Utilisateur non-root
   RUN useradd -m -u 1000 django

   WORKDIR /app

   # Installation des dépendances
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copie du code
   COPY . .

   # Permissions
   RUN chown -R django:django /app
   USER django

   # Port
   EXPOSE 8000

   # Entrypoint
   ENTRYPOINT ["/app/entrypoint.sh"]

**Entrypoint** : ``docker/django/entrypoint.sh``

.. code-block:: bash

   #!/bin/bash
   set -e

   # Attendre PostgreSQL
   echo "Waiting for PostgreSQL..."
   while ! nc -z postgresql 5432; do
     sleep 0.1
   done

   # Migrations
   echo "Running migrations..."
   python manage.py migrate --noinput

   # Collecte des fichiers statiques
   echo "Collecting static files..."
   python manage.py collectstatic --noinput

   # Créer un superuser si nécessaire
   python manage.py shell << EOF
   from django.contrib.auth import get_user_model
   User = get_user_model()
   if not User.objects.filter(username='admin').exists():
       User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
   EOF

   # Démarrer Gunicorn
   echo "Starting Gunicorn..."
   exec gunicorn SAE502.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers 4 \
       --timeout 60 \
       --access-logfile - \
       --error-logfile -

2. Nginx
~~~~~~~~

**Dockerfile** : ``docker/nginx/Dockerfile``

.. code-block:: dockerfile

   FROM nginx:alpine

   # Copier la configuration
   COPY nginx.conf /etc/nginx/nginx.conf

   # Créer les répertoires
   RUN mkdir -p /static /media

   EXPOSE 80 443

**Configuration** : ``docker/nginx/nginx.conf``

.. code-block:: nginx

   upstream django {
       server django-app:8000;
   }

   server {
       listen 80;
       server_name _;

       # Redirection HTTPS (production)
       # return 301 https://$host$request_uri;

       location /static/ {
           alias /static/;
           expires 30d;
           add_header Cache-Control "public, immutable";
       }

       location /media/ {
           alias /media/;
           expires 7d;
       }

       location / {
           proxy_pass http://django;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }

3. Monitoring
~~~~~~~~~~~~~

**Dockerfile** : ``docker/monitoring/Dockerfile``

.. code-block:: dockerfile

   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY healthcheck.py .

   CMD ["python", "healthcheck.py"]

**Script** : ``docker/monitoring/healthcheck.py``

.. code-block:: python

   import time
   import requests
   import psycopg2
   import redis
   import os

   def check_django():
       try:
           r = requests.get('http://django-app:8000/health/', timeout=5)
           return r.status_code == 200
       except:
           return False

   def check_postgresql():
       try:
           conn = psycopg2.connect(
               host='postgresql',
               database=os.getenv('DB_NAME'),
               user=os.getenv('DB_USER'),
               password=os.getenv('DB_PASSWORD')
           )
           conn.close()
           return True
       except:
           return False

   def check_redis():
       try:
           r = redis.Redis(host='redis', port=6379)
           return r.ping()
       except:
           return False

   while True:
       django_ok = check_django()
       postgres_ok = check_postgresql()
       redis_ok = check_redis()

       if not all([django_ok, postgres_ok, redis_ok]):
           # Envoyer une alerte
           print(f"ALERT: Django={django_ok}, PostgreSQL={postgres_ok}, Redis={redis_ok}")

       time.sleep(60)

Volumes
-------

Volumes nommés
~~~~~~~~~~~~~~

Les volumes Docker assurent la persistance des données :

.. code-block:: yaml

   volumes:
     postgres_data:
       driver: local
     redis_data:
       driver: local
     static:
       driver: local
     media:
       driver: local
     logs:
       driver: local

Volumes bind
~~~~~~~~~~~~

Pour le développement, le code est monté en bind mount :

.. code-block:: yaml

   services:
     django-app:
       volumes:
         - ../app:/app  # Code source en live reload

Réseau
------

Réseau par défaut
~~~~~~~~~~~~~~~~~

Docker Compose crée automatiquement un réseau bridge pour tous les services.

.. code-block:: yaml

   networks:
     default:
       name: sae502_network

Résolution DNS
~~~~~~~~~~~~~~

Les services peuvent se résoudre par leur nom :

* ``django-app`` → Application Django
* ``postgresql`` → Base de données
* ``redis`` → Cache
* ``nginx`` → Reverse proxy

Commandes utiles
----------------

Démarrage
~~~~~~~~~

.. code-block:: bash

   # Démarrer tous les services
   docker compose up -d

   # Démarrer avec rebuild
   docker compose up -d --build

   # Démarrer un service spécifique
   docker compose up -d django-app

Arrêt
~~~~~

.. code-block:: bash

   # Arrêter tous les services
   docker compose down

   # Arrêter et supprimer les volumes
   docker compose down -v

Logs
~~~~

.. code-block:: bash

   # Voir tous les logs
   docker compose logs -f

   # Logs d'un service spécifique
   docker compose logs -f django-app

   # Dernières 100 lignes
   docker compose logs --tail=100 django-app

Exécution de commandes
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Shell dans le conteneur Django
   docker compose exec django-app bash

   # Commande Django
   docker compose exec django-app python manage.py migrate

   # Shell PostgreSQL
   docker compose exec postgresql psql -U djangouser -d django_db

   # Redis CLI
   docker compose exec redis redis-cli

Inspection
~~~~~~~~~~

.. code-block:: bash

   # Statut des conteneurs
   docker compose ps

   # Utilisation des ressources
   docker stats

   # Inspecter un conteneur
   docker inspect sae502-django-app-1

Nettoyage
~~~~~~~~~

.. code-block:: bash

   # Supprimer les conteneurs arrêtés
   docker compose rm

   # Nettoyer les images non utilisées
   docker image prune

   # Nettoyer tout (ATTENTION !)
   docker system prune -a --volumes

Optimisations
-------------

Multi-stage builds
~~~~~~~~~~~~~~~~~~

Pour réduire la taille des images :

.. code-block:: dockerfile

   # Stage 1: Build
   FROM python:3.11 AS builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --user -r requirements.txt

   # Stage 2: Runtime
   FROM python:3.11-slim
   COPY --from=builder /root/.local /root/.local
   WORKDIR /app
   COPY . .
   CMD ["gunicorn", "SAE502.wsgi:application"]

Cache des layers
~~~~~~~~~~~~~~~~

Optimiser l'ordre des instructions pour maximiser le cache :

.. code-block:: dockerfile

   # ✅ Bon : requirements.txt change rarement
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .

   # ❌ Mauvais : invalide le cache à chaque changement
   COPY . .
   RUN pip install -r requirements.txt

Healthchecks
~~~~~~~~~~~~

Ajouter des healthchecks aux services :

.. code-block:: yaml

   services:
     django-app:
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 40s

Prochaines étapes
-----------------

* Déployez avec :doc:`ansible`
* Configurez la :doc:`security`
* Mettez en place le :doc:`monitoring`

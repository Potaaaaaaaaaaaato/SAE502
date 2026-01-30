Monitoring et Alertes
=====================

Cette page décrit le système de monitoring et d'alertes du projet SAE502.

Vue d'ensemble
--------------

Le projet inclut un système de monitoring complet qui surveille :

* ✅ Disponibilité de l'application Django
* ✅ État de la base de données PostgreSQL
* ✅ État du cache Redis
* ✅ Espace disque disponible
* ✅ Utilisation CPU et mémoire
* ✅ Logs d'erreurs

En cas de problème, des alertes sont envoyées par :

* 📧 Email
* 💬 Webhook (Slack, Discord, Teams)

Architecture
------------

.. code-block:: text

   ┌─────────────────┐
   │   Monitoring    │
   │   Container     │
   └────────┬────────┘
            │
            ├──► Django (healthcheck)
            ├──► PostgreSQL (connexion)
            ├──► Redis (ping)
            ├──► Disk (usage)
            └──► Logs (erreurs)
            
            ↓ (si problème)
            
   ┌─────────────────┐     ┌─────────────────┐
   │     Email       │     │    Webhook      │
   │   (SMTP)        │     │  (Slack/Discord)│
   └─────────────────┘     └─────────────────┘

Service de monitoring
---------------------

Container monitoring
~~~~~~~~~~~~~~~~~~~~

Le conteneur de monitoring s'exécute en continu :

.. code-block:: yaml

   monitoring:
     build: ./monitoring
     environment:
       - CHECK_INTERVAL=60
       - EMAIL_ALERTS=true
       - WEBHOOK_ALERTS=true
     depends_on:
       - django-app
       - postgresql
       - redis

Script healthcheck.py
~~~~~~~~~~~~~~~~~~~~~

Le script principal vérifie tous les services :

.. code-block:: python

   import time
   import requests
   import psycopg2
   import redis
   import os
   import smtplib
   from email.mime.text import MIMEText

   def check_django():
       """Vérifie la disponibilité de Django"""
       try:
           r = requests.get('http://django-app:8000/health/', timeout=5)
           return r.status_code == 200
       except Exception as e:
           return False

   def check_postgresql():
       """Vérifie la connexion PostgreSQL"""
       try:
           conn = psycopg2.connect(
               host='postgresql',
               database=os.getenv('DB_NAME'),
               user=os.getenv('DB_USER'),
               password=os.getenv('DB_PASSWORD'),
               connect_timeout=5
           )
           cursor = conn.cursor()
           cursor.execute('SELECT 1')
           conn.close()
           return True
       except Exception as e:
           return False

   def check_redis():
       """Vérifie la connexion Redis"""
       try:
           r = redis.Redis(host='redis', port=6379, socket_timeout=5)
           return r.ping()
       except Exception as e:
           return False

   def check_disk():
       """Vérifie l'espace disque"""
       import shutil
       total, used, free = shutil.disk_usage("/")
       percent = (used / total) * 100
       return {
           'percent': percent,
           'healthy': percent < 90
       }

   def send_alert(service, status):
       """Envoie une alerte"""
       send_email_alert(service, status)
       send_webhook_alert(service, status)

   def send_email_alert(service, status):
       """Envoie une alerte par email"""
       msg = MIMEText(f"Service {service} is {status}")
       msg['Subject'] = f"[ALERT] {service} - {status}"
       msg['From'] = os.getenv('EMAIL_FROM')
       msg['To'] = os.getenv('ALERT_EMAIL')

       with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
           server.starttls()
           server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
           server.send_message(msg)

   def send_webhook_alert(service, status):
       """Envoie une alerte via webhook"""
       webhook_url = os.getenv('WEBHOOK_URL')
       if webhook_url:
           payload = {
               'text': f'🚨 Alert: {service} is {status}',
               'service': service,
               'status': status
           }
           requests.post(webhook_url, json=payload)

   # Boucle principale
   while True:
       django_ok = check_django()
       postgres_ok = check_postgresql()
       redis_ok = check_redis()
       disk = check_disk()

       if not django_ok:
           send_alert('Django', 'DOWN')
       if not postgres_ok:
           send_alert('PostgreSQL', 'DOWN')
       if not redis_ok:
           send_alert('Redis', 'DOWN')
       if not disk['healthy']:
           send_alert('Disk', f"FULL ({disk['percent']:.1f}%)")

       time.sleep(int(os.getenv('CHECK_INTERVAL', 60)))

Endpoint healthcheck
--------------------

Django expose un endpoint ``/health/`` :

URL
~~~

.. code-block:: text

   GET /health/

Réponse (succès)
~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "django": "OK",
     "database": "OK",
     "redis": "OK",
     "disk": {
       "usage_percent": 45.2,
       "healthy": true
     },
     "status": "healthy",
     "timestamp": "2026-01-30T14:00:00Z"
   }

**Code HTTP** : ``200 OK``

Réponse (erreur)
~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "django": "OK",
     "database": "ERROR",
     "redis": "OK",
     "disk": {
       "usage_percent": 92.5,
       "healthy": false
     },
     "status": "unhealthy",
     "timestamp": "2026-01-30T14:00:00Z",
     "errors": [
       "PostgreSQL connection failed",
       "Disk usage above 90%"
     ]
   }

**Code HTTP** : ``503 Service Unavailable``

Implémentation Django
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # views.py
   from django.http import JsonResponse
   from django.db import connection
   from django.core.cache import cache
   import shutil
   from datetime import datetime

   def health_check(request):
       """Endpoint de healthcheck"""
       errors = []
       
       # Check Django
       django_ok = True
       
       # Check Database
       try:
           with connection.cursor() as cursor:
               cursor.execute("SELECT 1")
           database_ok = True
       except Exception as e:
           database_ok = False
           errors.append(f"Database error: {str(e)}")
       
       # Check Redis
       try:
           cache.set('health_check', 'ok', 10)
           redis_ok = cache.get('health_check') == 'ok'
       except Exception as e:
           redis_ok = False
           errors.append(f"Redis error: {str(e)}")
       
       # Check Disk
       total, used, free = shutil.disk_usage("/")
       disk_percent = (used / total) * 100
       disk_healthy = disk_percent < 90
       
       if not disk_healthy:
           errors.append(f"Disk usage: {disk_percent:.1f}%")
       
       # Status global
       all_ok = all([django_ok, database_ok, redis_ok, disk_healthy])
       
       response_data = {
           'django': 'OK' if django_ok else 'ERROR',
           'database': 'OK' if database_ok else 'ERROR',
           'redis': 'OK' if redis_ok else 'ERROR',
           'disk': {
               'usage_percent': round(disk_percent, 1),
               'healthy': disk_healthy
           },
           'status': 'healthy' if all_ok else 'unhealthy',
           'timestamp': datetime.utcnow().isoformat() + 'Z'
       }
       
       if errors:
           response_data['errors'] = errors
       
       status_code = 200 if all_ok else 503
       return JsonResponse(response_data, status=status_code)

Configuration des alertes
--------------------------

Email
~~~~~

Configuration dans ``.env`` :

.. code-block:: bash

   # SMTP Gmail
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password

   # Destinataire des alertes
   ALERT_EMAIL=admin@yourdomain.com
   EMAIL_FROM=monitoring@yourdomain.com

**Note** : Pour Gmail, créez un "App Password" dans les paramètres de sécurité.

Webhook Slack
~~~~~~~~~~~~~

1. Créer un webhook Slack :

   * Aller sur https://api.slack.com/apps
   * Créer une nouvelle app
   * Activer "Incoming Webhooks"
   * Copier l'URL du webhook

2. Configurer dans ``.env`` :

.. code-block:: bash

   WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

Format du message Slack :

.. code-block:: json

   {
     "text": "🚨 Alert: PostgreSQL is DOWN",
     "attachments": [
       {
         "color": "danger",
         "fields": [
           {
             "title": "Service",
             "value": "PostgreSQL",
             "short": true
           },
           {
             "title": "Status",
             "value": "DOWN",
             "short": true
           },
           {
             "title": "Timestamp",
             "value": "2026-01-30 14:00:00",
             "short": false
           }
         ]
       }
     ]
   }

Webhook Discord
~~~~~~~~~~~~~~~

1. Créer un webhook Discord :

   * Paramètres du serveur → Intégrations → Webhooks
   * Créer un webhook
   * Copier l'URL

2. Configurer dans ``.env`` :

.. code-block:: bash

   WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijklmnop

Format du message Discord :

.. code-block:: json

   {
     "content": "🚨 **Alert**: PostgreSQL is DOWN",
     "embeds": [
       {
         "title": "Service Health Alert",
         "color": 15158332,
         "fields": [
           {
             "name": "Service",
             "value": "PostgreSQL",
             "inline": true
           },
           {
             "name": "Status",
             "value": "DOWN",
             "inline": true
           }
         ],
         "timestamp": "2026-01-30T14:00:00.000Z"
       }
     ]
   }

Logs
----

Configuration Django
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'verbose': {
               'format': '{levelname} {asctime} {module} {message}',
               'style': '{',
           },
       },
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/app/logs/django.log',
               'maxBytes': 1024 * 1024 * 10,  # 10 MB
               'backupCount': 5,
               'formatter': 'verbose',
           },
           'error_file': {
               'level': 'ERROR',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/app/logs/django_errors.log',
               'maxBytes': 1024 * 1024 * 10,
               'backupCount': 5,
               'formatter': 'verbose',
           },
       },
       'loggers': {
           'django': {
               'handlers': ['file', 'error_file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }

Logs Nginx
~~~~~~~~~~

.. code-block:: nginx

   # Access log
   access_log /var/log/nginx/access.log combined;

   # Error log
   error_log /var/log/nginx/error.log warn;

Consulter les logs
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Logs Django
   docker compose logs -f django-app

   # Logs Nginx
   docker compose logs -f nginx

   # Logs PostgreSQL
   docker compose logs -f postgresql

   # Tous les logs
   docker compose logs -f

Métriques (optionnel)
---------------------

Pour un monitoring avancé, intégrez Prometheus + Grafana :

Prometheus
~~~~~~~~~~

.. code-block:: yaml

   prometheus:
     image: prom/prometheus
     volumes:
       - ./prometheus.yml:/etc/prometheus/prometheus.yml
       - prometheus_data:/prometheus
     ports:
       - "9090:9090"

Grafana
~~~~~~~

.. code-block:: yaml

   grafana:
     image: grafana/grafana
     volumes:
       - grafana_data:/var/lib/grafana
     ports:
       - "3000:3000"
     environment:
       - GF_SECURITY_ADMIN_PASSWORD=admin

Dashboards
~~~~~~~~~~

Grafana permet de créer des dashboards pour visualiser :

* Requêtes HTTP par seconde
* Temps de réponse
* Taux d'erreur
* Utilisation CPU/Mémoire
* Connexions base de données

Tests
-----

Tester le healthcheck
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test local
   curl http://localhost/health/

   # Test avec jq (formatage JSON)
   curl -s http://localhost/health/ | jq

Tester les alertes
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Arrêter PostgreSQL pour déclencher une alerte
   docker compose stop postgresql

   # Attendre 60 secondes (intervalle de check)
   # Vérifier la réception de l'alerte

   # Redémarrer PostgreSQL
   docker compose start postgresql

Simuler une alerte
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Script de test
   import requests

   webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK"
   
   payload = {
       'text': '🧪 Test Alert: This is a test',
       'service': 'Test',
       'status': 'TEST'
   }
   
   response = requests.post(webhook_url, json=payload)
   print(f"Status: {response.status_code}")

Bonnes pratiques
----------------

Checklist monitoring
~~~~~~~~~~~~~~~~~~~~

- [ ] Healthcheck endpoint configuré
- [ ] Service de monitoring actif
- [ ] Alertes email configurées
- [ ] Webhook configuré (Slack/Discord)
- [ ] Logs activés et rotatifs
- [ ] Intervalle de check approprié (60s)
- [ ] Tests des alertes effectués
- [ ] Documentation des procédures d'urgence

Intervalles recommandés
~~~~~~~~~~~~~~~~~~~~~~~

* **Healthcheck** : 60 secondes
* **Alertes** : Immédiat (dès détection)
* **Logs** : Rotation quotidienne ou à 10 MB
* **Métriques** : 15 secondes (si Prometheus)

Escalade
~~~~~~~~

Définissez une procédure d'escalade :

1. **Alerte automatique** → Email + Webhook
2. **Pas de réponse (15 min)** → SMS (optionnel)
3. **Pas de réponse (30 min)** → Appel téléphonique
4. **Incident critique** → Escalade immédiate

Prochaines étapes
-----------------

* Configurez les :doc:`backup`
* Renforcez la :doc:`security`
* Consultez la documentation :doc:`ansible`

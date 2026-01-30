Sécurité
========

Cette page décrit les mesures de sécurité implémentées dans le projet SAE502.

Vue d'ensemble
--------------

Le projet implémente plusieurs couches de sécurité pour protéger l'application en production :

* ✅ HTTPS obligatoire avec Let's Encrypt
* ✅ Headers de sécurité HTTP
* ✅ Isolation réseau Docker
* ✅ Utilisateurs non-root dans les conteneurs
* ✅ Firewall UFW
* ✅ Protection fail2ban
* ✅ Secrets chiffrés avec Ansible Vault
* ✅ SSH sécurisé (clés uniquement)

HTTPS / SSL/TLS
---------------

Certificats Let's Encrypt
~~~~~~~~~~~~~~~~~~~~~~~~~~

Les certificats SSL sont générés automatiquement avec Let's Encrypt :

.. code-block:: bash

   # Génération automatique via Ansible
   ansible-playbook -i inventories/production playbooks/04-ssl-letsencrypt.yml

**Renouvellement automatique** :

Un cron job renouvelle les certificats tous les jours à 3h du matin :

.. code-block:: bash

   0 3 * * * certbot renew --quiet

Configuration Nginx
~~~~~~~~~~~~~~~~~~~

Nginx force HTTPS et utilise des paramètres SSL sécurisés :

.. code-block:: nginx

   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ssl_prefer_server_ciphers on;

       # HSTS
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   }

Headers de sécurité
-------------------

Nginx ajoute automatiquement des headers de sécurité :

.. code-block:: nginx

   # HSTS - Force HTTPS
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

   # Empêche le clickjacking
   add_header X-Frame-Options "SAMEORIGIN" always;

   # Empêche le MIME sniffing
   add_header X-Content-Type-Options "nosniff" always;

   # XSS Protection
   add_header X-XSS-Protection "1; mode=block" always;

   # Content Security Policy
   add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

   # Referrer Policy
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;

Configuration Django
~~~~~~~~~~~~~~~~~~~~

Dans ``settings.py`` :

.. code-block:: python

   # Sécurité HTTPS
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True

   # HSTS
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True

   # Headers
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_BROWSER_XSS_FILTER = True
   X_FRAME_OPTIONS = 'SAMEORIGIN'

Isolation réseau
----------------

Docker Network
~~~~~~~~~~~~~~

Tous les services communiquent via un réseau Docker privé :

.. code-block:: yaml

   networks:
     default:
       name: sae502_network
       driver: bridge

**Isolation** :

* Seul Nginx est exposé publiquement (ports 80, 443)
* PostgreSQL, Redis, Django ne sont accessibles qu'entre conteneurs
* Pas d'accès direct depuis l'extérieur

Utilisateurs non-root
~~~~~~~~~~~~~~~~~~~~~

Tous les conteneurs s'exécutent avec des utilisateurs non-root :

.. code-block:: dockerfile

   # Django
   RUN useradd -m -u 1000 django
   USER django

   # Nginx
   USER nginx

   # PostgreSQL
   USER postgres

Firewall UFW
------------

Configuration
~~~~~~~~~~~~~

Le firewall UFW est configuré automatiquement par Ansible :

.. code-block:: bash

   # Autoriser SSH
   ufw allow 22/tcp

   # Autoriser HTTP/HTTPS
   ufw allow 80/tcp
   ufw allow 443/tcp

   # Bloquer tout le reste
   ufw default deny incoming
   ufw default allow outgoing

   # Activer le firewall
   ufw enable

Vérification
~~~~~~~~~~~~

.. code-block:: bash

   # Statut du firewall
   sudo ufw status verbose

   # Lister les règles
   sudo ufw status numbered

Fail2ban
--------

Configuration
~~~~~~~~~~~~~

Fail2ban protège contre les attaques par force brute :

**SSH** :

.. code-block:: ini

   [sshd]
   enabled = true
   port = 22
   filter = sshd
   logpath = /var/log/auth.log
   maxretry = 3
   bantime = 3600

**Nginx** :

.. code-block:: ini

   [nginx-http-auth]
   enabled = true
   filter = nginx-http-auth
   port = http,https
   logpath = /var/log/nginx/error.log
   maxretry = 5
   bantime = 3600

Vérification
~~~~~~~~~~~~

.. code-block:: bash

   # Statut fail2ban
   sudo fail2ban-client status

   # Statut d'une jail spécifique
   sudo fail2ban-client status sshd

   # Débannir une IP
   sudo fail2ban-client set sshd unbanip 192.168.1.100

SSH sécurisé
------------

Configuration
~~~~~~~~~~~~~

Le fichier ``/etc/ssh/sshd_config`` est sécurisé :

.. code-block:: bash

   # Désactiver l'accès root
   PermitRootLogin no

   # Authentification par clés uniquement
   PasswordAuthentication no
   PubkeyAuthentication yes

   # Désactiver les méthodes d'authentification faibles
   ChallengeResponseAuthentication no
   UsePAM yes

   # Limiter les utilisateurs
   AllowUsers deployer

   # Changer le port (optionnel)
   Port 2222

Clés SSH
~~~~~~~~

.. code-block:: bash

   # Générer une paire de clés
   ssh-keygen -t ed25519 -C "your-email@example.com"

   # Copier la clé publique sur le serveur
   ssh-copy-id -i ~/.ssh/id_ed25519.pub deployer@your-server

   # Se connecter
   ssh -i ~/.ssh/id_ed25519 deployer@your-server

Secrets et variables sensibles
-------------------------------

Ansible Vault
~~~~~~~~~~~~~

Les secrets sont chiffrés avec Ansible Vault :

.. code-block:: bash

   # Créer un fichier vault
   ansible-vault create group_vars/production/vault.yml

   # Éditer le vault
   ansible-vault edit group_vars/production/vault.yml

   # Contenu du vault
   vault_django_secret_key: "votre-cle-secrete"
   vault_db_password: "mot-de-passe-db"
   vault_smtp_password: "app-password"

Variables d'environnement
~~~~~~~~~~~~~~~~~~~~~~~~~~

Les secrets ne sont jamais en dur dans le code :

.. code-block:: python

   # ✅ Bon
   SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

   # ❌ Mauvais
   SECRET_KEY = 'ma-cle-secrete-en-dur'

Fichier .env
~~~~~~~~~~~~

Le fichier ``.env`` contient les secrets et n'est jamais commité :

.. code-block:: bash

   # .gitignore
   .env
   .env.local
   .env.production

Django Security
---------------

Configuration settings.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Mode production
   DEBUG = False

   # Hosts autorisés
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

   # Secret key
   SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

   # Base de données
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DB_NAME'),
           'USER': os.environ.get('DB_USER'),
           'PASSWORD': os.environ.get('DB_PASSWORD'),
           'HOST': os.environ.get('DB_HOST'),
           'PORT': os.environ.get('DB_PORT'),
       }
   }

   # CSRF
   CSRF_COOKIE_HTTPONLY = True
   CSRF_COOKIE_SECURE = True

   # Sessions
   SESSION_COOKIE_HTTPONLY = True
   SESSION_COOKIE_SECURE = True
   SESSION_COOKIE_SAMESITE = 'Strict'

Protection CSRF
~~~~~~~~~~~~~~~

Django protège automatiquement contre les attaques CSRF :

.. code-block:: html

   <form method="post">
       {% csrf_token %}
       <!-- Formulaire -->
   </form>

Protection XSS
~~~~~~~~~~~~~~

Les templates Django échappent automatiquement les variables :

.. code-block:: html

   <!-- ✅ Sécurisé (échappé automatiquement) -->
   <p>{{ user_input }}</p>

   <!-- ❌ Dangereux (pas d'échappement) -->
   <p>{{ user_input|safe }}</p>

Protection SQL Injection
~~~~~~~~~~~~~~~~~~~~~~~~

Utilisez toujours l'ORM Django :

.. code-block:: python

   # ✅ Sécurisé (ORM)
   User.objects.filter(username=username)

   # ❌ Dangereux (SQL brut)
   cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

Backups sécurisés
-----------------

Chiffrement
~~~~~~~~~~~

Les backups sont chiffrés avant stockage :

.. code-block:: bash

   # Backup avec chiffrement GPG
   pg_dump django_db | gzip | gpg --encrypt --recipient admin@example.com > backup.sql.gz.gpg

   # Restauration
   gpg --decrypt backup.sql.gz.gpg | gunzip | psql django_db

Stockage distant
~~~~~~~~~~~~~~~~

Les backups sont copiés sur un serveur distant :

.. code-block:: bash

   # Copie sécurisée via SCP
   scp backup.sql.gz.gpg backup-server:/backups/

   # Ou via rsync
   rsync -avz --delete /backups/ backup-server:/backups/

Audit et logs
-------------

Logs applicatifs
~~~~~~~~~~~~~~~~

Django enregistre tous les événements importants :

.. code-block:: python

   LOGGING = {
       'version': 1,
       'handlers': {
           'file': {
               'class': 'logging.FileHandler',
               'filename': '/app/logs/django.log',
           },
       },
       'loggers': {
           'django': {
               'handlers': ['file'],
               'level': 'INFO',
           },
       },
   }

Logs système
~~~~~~~~~~~~

Les logs système sont conservés et analysés :

.. code-block:: bash

   # Logs SSH
   /var/log/auth.log

   # Logs Nginx
   /var/log/nginx/access.log
   /var/log/nginx/error.log

   # Logs fail2ban
   /var/log/fail2ban.log

Bonnes pratiques
----------------

Checklist de sécurité
~~~~~~~~~~~~~~~~~~~~~

- [ ] HTTPS activé avec certificats valides
- [ ] Headers de sécurité configurés
- [ ] Firewall UFW activé
- [ ] fail2ban configuré
- [ ] SSH sécurisé (clés uniquement, pas de root)
- [ ] Secrets chiffrés (Ansible Vault)
- [ ] DEBUG=False en production
- [ ] ALLOWED_HOSTS configuré
- [ ] Backups chiffrés et testés
- [ ] Logs activés et surveillés
- [ ] Mises à jour de sécurité automatiques

Mises à jour
~~~~~~~~~~~~

Configurez les mises à jour automatiques de sécurité :

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades

Monitoring de sécurité
~~~~~~~~~~~~~~~~~~~~~~

Surveillez les événements de sécurité :

* Tentatives de connexion SSH échouées
* Requêtes HTTP suspectes
* Utilisation anormale des ressources
* Modifications de fichiers système

Prochaines étapes
-----------------

* Configurez le :doc:`monitoring`
* Mettez en place les :doc:`backup`
* Consultez la documentation :doc:`ansible`

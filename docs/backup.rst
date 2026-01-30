Backups et Restauration
========================

Cette page décrit le système de backups automatiques et les procédures de restauration.

Vue d'ensemble
--------------

Le projet implémente un système de backups complet pour :

* ✅ Base de données PostgreSQL (quotidien)
* ✅ Fichiers media uploadés (hebdomadaire)
* ✅ Configuration et secrets (manuel)
* ✅ Rotation automatique (7 jours)
* ✅ Chiffrement des backups (optionnel)
* ✅ Stockage distant (optionnel)

Architecture
------------

.. code-block:: text

   ┌─────────────────┐
   │   Cron Job      │  (2h du matin)
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Backup Script  │
   └────────┬────────┘
            │
            ├──► PostgreSQL dump
            ├──► Media files tar
            └──► Configuration backup
            
            ↓
            
   ┌─────────────────┐     ┌─────────────────┐
   │  Local Storage  │────►│ Remote Storage  │
   │   /backups/     │     │   (optionnel)   │
   └─────────────────┘     └─────────────────┘

Backup PostgreSQL
-----------------

Script de backup
~~~~~~~~~~~~~~~~

**Fichier** : ``scripts/backup.sh``

.. code-block:: bash

   #!/bin/bash
   set -e

   # Configuration
   BACKUP_DIR="/backups/postgres"
   RETENTION_DAYS=7
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

   # Créer le répertoire si nécessaire
   mkdir -p "$BACKUP_DIR"

   # Backup PostgreSQL
   echo "Starting PostgreSQL backup..."
   docker compose exec -T postgresql pg_dump \
       -U "$DB_USER" \
       -d "$DB_NAME" \
       --format=custom \
       --compress=9 \
       > "$BACKUP_FILE"

   # Vérifier le backup
   if [ -f "$BACKUP_FILE" ]; then
       SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
       echo "Backup completed: $BACKUP_FILE ($SIZE)"
   else
       echo "ERROR: Backup failed!"
       exit 1
   fi

   # Rotation des backups (garder 7 jours)
   echo "Cleaning old backups..."
   find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

   # Lister les backups
   echo "Available backups:"
   ls -lh "$BACKUP_DIR"

   echo "Backup completed successfully!"

Rendre le script exécutable :

.. code-block:: bash

   chmod +x scripts/backup.sh

Exécution manuelle
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Depuis le répertoire docker/
   cd docker
   ../scripts/backup.sh

Configuration automatique
~~~~~~~~~~~~~~~~~~~~~~~~~

Le playbook Ansible configure un cron job :

**Fichier** : ``playbooks/07-backup-database.yml``

.. code-block:: yaml

   ---
   - name: Configurer les backups automatiques
     hosts: all
     become: yes
     tasks:
       - name: Créer le répertoire de backups
         file:
           path: /backups/postgres
           state: directory
           owner: "{{ deploy_user }}"
           mode: '0700'

       - name: Copier le script de backup
         copy:
           src: ../scripts/backup.sh
           dest: /usr/local/bin/backup-postgres.sh
           mode: '0755'

       - name: Configurer le cron job
         cron:
           name: "Backup PostgreSQL quotidien"
           minute: "0"
           hour: "2"
           job: "/usr/local/bin/backup-postgres.sh >> /var/log/backup.log 2>&1"
           user: "{{ deploy_user }}"

Vérification des backups
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Lister les backups
   ls -lh /backups/postgres/

   # Vérifier l'intégrité d'un backup
   docker compose exec postgresql pg_restore \
       --list \
       /backups/postgres/backup_20260130_020000.sql.gz

Restauration PostgreSQL
-----------------------

Script de restauration
~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``scripts/restore.sh``

.. code-block:: bash

   #!/bin/bash
   set -e

   # Vérifier l'argument
   if [ -z "$1" ]; then
       echo "Usage: $0 <backup_file>"
       echo "Example: $0 /backups/postgres/backup_20260130_020000.sql.gz"
       exit 1
   fi

   BACKUP_FILE="$1"

   # Vérifier que le fichier existe
   if [ ! -f "$BACKUP_FILE" ]; then
       echo "ERROR: Backup file not found: $BACKUP_FILE"
       exit 1
   fi

   echo "WARNING: This will replace the current database!"
   echo "Backup file: $BACKUP_FILE"
   read -p "Continue? (yes/no): " CONFIRM

   if [ "$CONFIRM" != "yes" ]; then
       echo "Restoration cancelled."
       exit 0
   fi

   # Arrêter l'application
   echo "Stopping application..."
   docker compose stop django-app

   # Restaurer la base de données
   echo "Restoring database..."
   docker compose exec -T postgresql pg_restore \
       -U "$DB_USER" \
       -d "$DB_NAME" \
       --clean \
       --if-exists \
       < "$BACKUP_FILE"

   # Redémarrer l'application
   echo "Starting application..."
   docker compose start django-app

   echo "Restoration completed successfully!"

Rendre le script exécutable :

.. code-block:: bash

   chmod +x scripts/restore.sh

Exécution
~~~~~~~~~

.. code-block:: bash

   # Restaurer un backup
   cd docker
   ../scripts/restore.sh /backups/postgres/backup_20260130_020000.sql.gz

Procédure de restauration complète
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Arrêter l'application** :

.. code-block:: bash

   docker compose stop django-app

2. **Supprimer la base de données actuelle** (optionnel) :

.. code-block:: bash

   docker compose exec postgresql psql -U postgres -c "DROP DATABASE django_db;"
   docker compose exec postgresql psql -U postgres -c "CREATE DATABASE django_db OWNER djangouser;"

3. **Restaurer le backup** :

.. code-block:: bash

   docker compose exec -T postgresql pg_restore \
       -U djangouser \
       -d django_db \
       --clean \
       --if-exists \
       < /backups/postgres/backup_20260130_020000.sql.gz

4. **Redémarrer l'application** :

.. code-block:: bash

   docker compose start django-app

5. **Vérifier** :

.. code-block:: bash

   curl http://localhost/health/

Backup des fichiers media
--------------------------

Script de backup media
~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``scripts/backup-media.sh``

.. code-block:: bash

   #!/bin/bash
   set -e

   # Configuration
   BACKUP_DIR="/backups/media"
   MEDIA_DIR="/path/to/media"
   RETENTION_DAYS=30
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="$BACKUP_DIR/media_$TIMESTAMP.tar.gz"

   # Créer le répertoire
   mkdir -p "$BACKUP_DIR"

   # Backup des fichiers media
   echo "Starting media backup..."
   tar -czf "$BACKUP_FILE" -C "$MEDIA_DIR" .

   # Vérifier
   if [ -f "$BACKUP_FILE" ]; then
       SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
       echo "Media backup completed: $BACKUP_FILE ($SIZE)"
   else
       echo "ERROR: Media backup failed!"
       exit 1
   fi

   # Rotation
   find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

   echo "Media backup completed successfully!"

Cron job hebdomadaire
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Tous les dimanches à 3h du matin
   0 3 * * 0 /usr/local/bin/backup-media.sh >> /var/log/backup-media.log 2>&1

Restauration media
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Restaurer les fichiers media
   tar -xzf /backups/media/media_20260130_030000.tar.gz -C /path/to/media/

Backup de la configuration
---------------------------

Fichiers à sauvegarder
~~~~~~~~~~~~~~~~~~~~~~

* ``.env`` - Variables d'environnement
* ``docker-compose.yml`` - Configuration Docker
* ``nginx.conf`` - Configuration Nginx
* Certificats SSL (si auto-signés)
* Ansible Vault (chiffré)

Script de backup config
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   set -e

   BACKUP_DIR="/backups/config"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

   mkdir -p "$BACKUP_DIR"

   # Backup de la configuration
   tar -czf "$BACKUP_FILE" \
       docker/.env \
       docker/docker-compose.yml \
       docker/nginx/nginx.conf \
       ansible/group_vars/

   echo "Configuration backup: $BACKUP_FILE"

Chiffrement des backups
------------------------

Avec GPG
~~~~~~~~

.. code-block:: bash

   # Générer une clé GPG
   gpg --gen-key

   # Chiffrer un backup
   gpg --encrypt --recipient admin@example.com backup.sql.gz

   # Déchiffrer
   gpg --decrypt backup.sql.gz.gpg > backup.sql.gz

Avec OpenSSL
~~~~~~~~~~~~

.. code-block:: bash

   # Chiffrer
   openssl enc -aes-256-cbc -salt -in backup.sql.gz -out backup.sql.gz.enc

   # Déchiffrer
   openssl enc -aes-256-cbc -d -in backup.sql.gz.enc -out backup.sql.gz

Stockage distant
----------------

Via SCP
~~~~~~~

.. code-block:: bash

   # Copier vers un serveur distant
   scp /backups/postgres/backup_*.sql.gz backup-server:/backups/

   # Avec clé SSH
   scp -i ~/.ssh/backup_key /backups/postgres/backup_*.sql.gz \
       backup-user@backup-server:/backups/

Via rsync
~~~~~~~~~

.. code-block:: bash

   # Synchronisation
   rsync -avz --delete \
       /backups/ \
       backup-server:/backups/

   # Avec SSH
   rsync -avz -e "ssh -i ~/.ssh/backup_key" \
       /backups/ \
       backup-user@backup-server:/backups/

Vers S3 (AWS)
~~~~~~~~~~~~~

.. code-block:: bash

   # Installer AWS CLI
   pip install awscli

   # Configurer
   aws configure

   # Upload vers S3
   aws s3 cp /backups/postgres/backup_20260130_020000.sql.gz \
       s3://my-backup-bucket/postgres/

   # Sync complet
   aws s3 sync /backups/ s3://my-backup-bucket/

Script automatique
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # backup-and-upload.sh

   # Backup local
   /usr/local/bin/backup-postgres.sh

   # Upload vers S3
   LATEST_BACKUP=$(ls -t /backups/postgres/backup_*.sql.gz | head -1)
   aws s3 cp "$LATEST_BACKUP" s3://my-backup-bucket/postgres/

   echo "Backup uploaded to S3: $LATEST_BACKUP"

Tests de restauration
---------------------

Il est crucial de tester régulièrement les restaurations !

Procédure de test
~~~~~~~~~~~~~~~~~

1. **Créer un environnement de test** :

.. code-block:: bash

   # Copier docker-compose.yml
   cp docker-compose.yml docker-compose.test.yml

   # Modifier les ports
   sed -i 's/80:80/8080:80/g' docker-compose.test.yml

2. **Démarrer l'environnement de test** :

.. code-block:: bash

   docker compose -f docker-compose.test.yml up -d

3. **Restaurer le backup** :

.. code-block:: bash

   docker compose -f docker-compose.test.yml exec -T postgresql pg_restore \
       -U djangouser -d django_db < /backups/postgres/backup_latest.sql.gz

4. **Vérifier** :

.. code-block:: bash

   curl http://localhost:8080/health/

5. **Nettoyer** :

.. code-block:: bash

   docker compose -f docker-compose.test.yml down -v

Monitoring des backups
----------------------

Vérifier les backups
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Script de vérification
   #!/bin/bash

   BACKUP_DIR="/backups/postgres"
   LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.sql.gz | head -1)

   if [ -z "$LATEST_BACKUP" ]; then
       echo "ERROR: No backups found!"
       exit 1
   fi

   # Vérifier l'âge du backup
   BACKUP_AGE=$(find "$LATEST_BACKUP" -mtime +1)
   if [ -n "$BACKUP_AGE" ]; then
       echo "WARNING: Latest backup is older than 24 hours!"
       exit 1
   fi

   echo "OK: Latest backup is recent: $LATEST_BACKUP"

Alertes
~~~~~~~

Intégrer dans le monitoring :

.. code-block:: python

   def check_backups():
       """Vérifie que les backups sont à jour"""
       import os
       from datetime import datetime, timedelta

       backup_dir = "/backups/postgres"
       files = os.listdir(backup_dir)
       
       if not files:
           return False
       
       latest = max(files, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
       latest_path = os.path.join(backup_dir, latest)
       
       # Vérifier que le backup a moins de 25 heures
       mtime = datetime.fromtimestamp(os.path.getmtime(latest_path))
       age = datetime.now() - mtime
       
       return age < timedelta(hours=25)

Bonnes pratiques
----------------

Checklist backups
~~~~~~~~~~~~~~~~~

- [ ] Backups PostgreSQL quotidiens configurés
- [ ] Backups media hebdomadaires configurés
- [ ] Rotation des backups (7-30 jours)
- [ ] Chiffrement activé (si sensible)
- [ ] Stockage distant configuré
- [ ] Tests de restauration mensuels
- [ ] Monitoring des backups actif
- [ ] Documentation à jour

Règle 3-2-1
~~~~~~~~~~~

Suivez la règle **3-2-1** pour les backups :

* **3** copies des données
* **2** supports différents (disque local + cloud)
* **1** copie hors site (distant)

Rétention
~~~~~~~~~

Politique de rétention recommandée :

* **Quotidien** : 7 jours
* **Hebdomadaire** : 4 semaines
* **Mensuel** : 12 mois
* **Annuel** : 5 ans (si requis)

Prochaines étapes
-----------------

* Configurez le :doc:`monitoring`
* Renforcez la :doc:`security`
* Consultez la documentation :doc:`ansible`

Installation
============

Cette page décrit comment installer et démarrer le projet SAE502 en local ou en production.

Prérequis
---------

Avant de commencer, assurez-vous d'avoir installé :

* **Docker** 24.0 ou supérieur
* **Docker Compose** 2.20 ou supérieur
* **Git**
* **Ansible** 2.9+ (pour le déploiement en production)

Installation locale (développement)
------------------------------------

1. Cloner le repository
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone <votre-repo>
   cd SAE502

2. Configurer les variables d'environnement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docker
   cp .env.local .env
   # Optionnel : modifier les variables dans .env

Le fichier ``.env`` contient toutes les variables de configuration nécessaires :

.. code-block:: bash

   # Django
   DEBUG=True
   DJANGO_SECRET_KEY=votre-cle-secrete-dev
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Base de données
   DB_NAME=django_db
   DB_USER=djangouser
   DB_PASSWORD=mot-de-passe-dev

3. Lancer les conteneurs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker compose up -d --build

Cette commande va :

* Construire les images Docker
* Démarrer tous les services (Django, PostgreSQL, Redis, Nginx, Monitoring)
* Exécuter les migrations Django
* Collecter les fichiers statiques

4. Vérifier que tout fonctionne
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Voir le statut des conteneurs
   docker compose ps

   # Voir les logs
   docker compose logs -f

   # Accéder à l'application
   open http://localhost

5. Accéder aux différentes pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Une fois l'application démarrée, vous pouvez accéder à :

* **Page d'accueil** : http://localhost
* **Démonstration** : http://localhost/demo/
* **Healthcheck** : http://localhost/health/
* **Admin Django** : http://localhost/admin/ (admin/admin123)

Arrêter les services
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker compose down

Pour supprimer également les volumes (données) :

.. code-block:: bash

   docker compose down -v

Installation en production
---------------------------

Pour un déploiement en production, utilisez Ansible. Voir la section :doc:`ansible` pour plus de détails.

Déploiement rapide avec Ansible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Configurer l'inventaire
   vi ansible/inventories/production/hosts

   # Lancer le déploiement complet
   ansible-playbook -i ansible/inventories/production ansible/site.yml

Test local avec Multipass
--------------------------

Pour tester le déploiement Ansible localement sans serveur distant :

.. code-block:: bash

   # Créer la VM
   multipass launch --name sae502-test -c 2 -m 2G -d 20G

   # Configurer SSH
   cd ansible
   ./setup-multipass-ssh.sh

   # Déploiement complet
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

Dépannage
---------

Problèmes courants
~~~~~~~~~~~~~~~~~~

**Les conteneurs ne démarrent pas**

.. code-block:: bash

   # Vérifier les logs
   docker compose logs

   # Reconstruire les images
   docker compose build --no-cache
   docker compose up -d

**Erreur de connexion à la base de données**

Vérifiez que PostgreSQL est bien démarré :

.. code-block:: bash

   docker compose ps postgresql
   docker compose logs postgresql

**Port déjà utilisé**

Si le port 80 ou 443 est déjà utilisé, modifiez le fichier ``docker-compose.yml`` :

.. code-block:: yaml

   nginx:
     ports:
       - "8080:80"  # Au lieu de 80:80
       - "8443:443" # Au lieu de 443:443

Prochaines étapes
-----------------

* Consultez l':doc:`architecture` pour comprendre la structure du projet
* Configurez :doc:`docker` pour personnaliser les services
* Déployez en production avec :doc:`ansible`

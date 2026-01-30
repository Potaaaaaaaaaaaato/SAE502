Documentation Ansible
=====================

Cette page décrit l'utilisation d'Ansible pour automatiser le déploiement du projet SAE502.

Vue d'ensemble
--------------

Ansible permet de déployer l'application complète sur un serveur vierge en une seule commande.

Le déploiement automatise :

* ✅ Préparation du serveur (utilisateurs, dépendances)
* ✅ Installation de Docker et Docker Compose
* ✅ Déploiement de l'application
* ✅ Configuration SSL/TLS avec Let's Encrypt
* ✅ Sécurisation (UFW, fail2ban, SSH)
* ✅ Monitoring et alertes
* ✅ Backups automatiques

Structure Ansible
-----------------

.. code-block:: text

   ansible/
   ├── site.yml                      # Playbook master
   ├── ansible.cfg                   # Configuration Ansible
   ├── setup-multipass-ssh.sh        # Script SSH Multipass
   ├── playbooks/                    # Playbooks modulaires
   │   ├── 01-prepare-host.yml
   │   ├── 02-install-docker.yml
   │   ├── 03-deploy-application.yml
   │   ├── 04-ssl-letsencrypt.yml
   │   ├── 04-ssl-letsencrypt-conditional.yml
   │   ├── 05-security-hardening.yml
   │   ├── 06-monitoring-alerting.yml
   │   └── 07-backup-database.yml
   ├── inventories/
   │   ├── production/
   │   │   └── hosts
   │   └── multipass/
   │       ├── hosts
   │       └── group_vars/all.yml
   ├── group_vars/
   │   └── all.yml                   # Variables globales
   └── templates/                    # Templates Jinja2

Playbooks
---------

1. Préparation de l'hôte
~~~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``playbooks/01-prepare-host.yml``

Ce playbook prépare le serveur :

* Mise à jour des paquets système
* Installation des dépendances (git, curl, etc.)
* Création de l'utilisateur de déploiement
* Configuration SSH
* Installation de Python

.. code-block:: yaml

   ---
   - name: Préparer l'hôte pour le déploiement
     hosts: all
     become: yes
     tasks:
       - name: Mise à jour du cache APT
         apt:
           update_cache: yes
           cache_valid_time: 3600

       - name: Installation des dépendances
         apt:
           name:
             - git
             - curl
             - vim
             - htop
             - python3-pip
           state: present

       - name: Créer l'utilisateur de déploiement
         user:
           name: "{{ deploy_user }}"
           shell: /bin/bash
           groups: sudo
           append: yes

2. Installation Docker
~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``playbooks/02-install-docker.yml``

Installation de Docker et Docker Compose :

* Ajout du repository Docker officiel
* Installation de Docker Engine
* Installation de Docker Compose
* Configuration du daemon Docker
* Ajout de l'utilisateur au groupe docker

.. code-block:: yaml

   ---
   - name: Installer Docker et Docker Compose
     hosts: all
     become: yes
     tasks:
       - name: Installer les prérequis Docker
         apt:
           name:
             - apt-transport-https
             - ca-certificates
             - gnupg
             - lsb-release
           state: present

       - name: Ajouter la clé GPG Docker
         apt_key:
           url: https://download.docker.com/linux/ubuntu/gpg
           state: present

       - name: Installer Docker
         apt:
           name:
             - docker-ce
             - docker-ce-cli
             - containerd.io
           state: present

       - name: Installer Docker Compose
         get_url:
           url: "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64"
           dest: /usr/local/bin/docker-compose
           mode: '0755'

3. Déploiement de l'application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``playbooks/03-deploy-application.yml``

Déploiement de l'application Django :

* Clone du repository Git
* Copie des fichiers de configuration
* Configuration des variables d'environnement
* Démarrage des conteneurs Docker
* Exécution des migrations Django

.. code-block:: yaml

   ---
   - name: Déployer l'application Django
     hosts: all
     become: yes
     tasks:
       - name: Cloner le repository
         git:
           repo: "{{ git_repo }}"
           dest: "{{ app_dir }}"
           version: "{{ git_branch }}"

       - name: Copier le fichier .env
         template:
           src: templates/env.j2
           dest: "{{ app_dir }}/docker/.env"
           mode: '0600'

       - name: Démarrer les conteneurs
         docker_compose:
           project_src: "{{ app_dir }}/docker"
           state: present
           pull: yes

4. SSL Let's Encrypt
~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``playbooks/04-ssl-letsencrypt.yml``

Configuration HTTPS avec Let's Encrypt :

* Installation de Certbot
* Génération des certificats SSL
* Configuration du renouvellement automatique
* Configuration Nginx pour HTTPS

.. code-block:: yaml

   ---
   - name: Configurer SSL avec Let's Encrypt
     hosts: all
     become: yes
     tasks:
       - name: Installer Certbot
         apt:
           name:
             - certbot
             - python3-certbot-nginx
           state: present

       - name: Générer le certificat SSL
         command: >
           certbot certonly --nginx
           --non-interactive
           --agree-tos
           --email {{ admin_email }}
           -d {{ domain_name }}

       - name: Configurer le renouvellement automatique
         cron:
           name: "Renouvellement SSL"
           minute: "0"
           hour: "3"
           job: "certbot renew --quiet"

5. Sécurisation
~~~~~~~~~~~~~~~

**Fichier** : ``playbooks/05-security-hardening.yml``

Renforcement de la sécurité :

* Configuration du firewall UFW
* Installation et configuration de fail2ban
* Désactivation de l'accès root SSH
* Configuration SSH (clés uniquement)
* Mise à jour automatique des paquets de sécurité

.. code-block:: yaml

   ---
   - name: Sécuriser le serveur
     hosts: all
     become: yes
     tasks:
       - name: Installer UFW
         apt:
           name: ufw
           state: present

       - name: Configurer UFW
         ufw:
           rule: allow
           port: "{{ item }}"
         loop:
           - "22"
           - "80"
           - "443"

       - name: Activer UFW
         ufw:
           state: enabled

       - name: Installer fail2ban
         apt:
           name: fail2ban
           state: present

6. Monitoring
~~~~~~~~~~~~~

**Fichier** : ``playbooks/06-monitoring-alerting.yml``

Configuration du monitoring :

* Configuration des healthchecks
* Configuration des alertes email
* Configuration des webhooks (Slack/Discord)
* Installation d'outils de monitoring (optionnel)

7. Backups
~~~~~~~~~~

**Fichier** : ``playbooks/07-backup-database.yml``

Configuration des backups automatiques :

* Script de backup PostgreSQL
* Configuration cron pour backups quotidiens
* Rotation des backups (7 jours)
* Backup des fichiers media

Inventaires
-----------

Production
~~~~~~~~~~

**Fichier** : ``inventories/production/hosts``

.. code-block:: ini

   [webservers]
   production-server ansible_host=your-server-ip ansible_user=ubuntu

   [all:vars]
   ansible_python_interpreter=/usr/bin/python3

Multipass (test local)
~~~~~~~~~~~~~~~~~~~~~~~

**Fichier** : ``inventories/multipass/hosts``

.. code-block:: ini

   [webservers]
   sae502-test ansible_host=192.168.64.X ansible_user=ubuntu

Variables
---------

Variables globales
~~~~~~~~~~~~~~~~~~

**Fichier** : ``group_vars/all.yml``

.. code-block:: yaml

   # Application
   app_name: sae502
   app_dir: /opt/sae502
   deploy_user: deployer

   # Git
   git_repo: https://github.com/username/SAE502.git
   git_branch: main

   # Django
   django_secret_key: "{{ vault_django_secret_key }}"
   django_debug: false
   allowed_hosts: "{{ domain_name }}"

   # Base de données
   db_name: django_db
   db_user: djangouser
   db_password: "{{ vault_db_password }}"

   # Email
   admin_email: admin@yourdomain.com
   smtp_host: smtp.gmail.com
   smtp_user: "{{ vault_smtp_user }}"
   smtp_password: "{{ vault_smtp_password }}"

   # SSL
   domain_name: yourdomain.com

Ansible Vault
~~~~~~~~~~~~~

Pour sécuriser les secrets :

.. code-block:: bash

   # Créer un fichier vault
   ansible-vault create group_vars/production/vault.yml

   # Éditer le vault
   ansible-vault edit group_vars/production/vault.yml

   # Contenu du vault
   vault_django_secret_key: "votre-cle-secrete"
   vault_db_password: "mot-de-passe-db"
   vault_smtp_user: "email@gmail.com"
   vault_smtp_password: "app-password"

Déploiement
-----------

Déploiement complet
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Production
   ansible-playbook -i inventories/production ansible/site.yml --ask-vault-pass

   # Multipass (test)
   ansible-playbook -i inventories/multipass/hosts ansible/site.yml

Déploiement par étapes
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Seulement la préparation
   ansible-playbook -i inventories/production playbooks/01-prepare-host.yml

   # Seulement Docker
   ansible-playbook -i inventories/production playbooks/02-install-docker.yml

   # Seulement l'application
   ansible-playbook -i inventories/production playbooks/03-deploy-application.yml

Tags
~~~~

Utiliser des tags pour exécuter des tâches spécifiques :

.. code-block:: bash

   # Seulement les tâches de sécurité
   ansible-playbook -i inventories/production ansible/site.yml --tags security

   # Seulement les backups
   ansible-playbook -i inventories/production ansible/site.yml --tags backup

Mode check
~~~~~~~~~~

Tester sans appliquer les changements :

.. code-block:: bash

   ansible-playbook -i inventories/production ansible/site.yml --check

Test avec Multipass
-------------------

Multipass permet de tester le déploiement localement sur macOS/Linux.

1. Créer la VM
~~~~~~~~~~~~~~

.. code-block:: bash

   multipass launch --name sae502-test -c 2 -m 2G -d 20G

2. Configurer SSH
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ansible
   ./setup-multipass-ssh.sh

3. Déployer
~~~~~~~~~~~

.. code-block:: bash

   ansible-playbook -i inventories/multipass/hosts \
     playbooks/01-prepare-host.yml \
     playbooks/02-install-docker.yml \
     playbooks/03-deploy-application.yml \
     playbooks/04-ssl-letsencrypt-conditional.yml \
     playbooks/05-security-hardening.yml \
     playbooks/06-monitoring-alerting.yml \
     playbooks/07-backup-database.yml

4. Accéder à l'application
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Obtenir l'IP de la VM
   multipass info sae502-test

   # Accéder via navigateur
   open http://IP-DE-LA-VM

5. Nettoyer
~~~~~~~~~~~

.. code-block:: bash

   # Arrêter la VM
   multipass stop sae502-test

   # Supprimer la VM
   multipass delete sae502-test
   multipass purge

Commandes utiles
----------------

.. code-block:: bash

   # Lister les hôtes
   ansible all -i inventories/production --list-hosts

   # Ping les hôtes
   ansible all -i inventories/production -m ping

   # Exécuter une commande ad-hoc
   ansible all -i inventories/production -a "uptime"

   # Vérifier la syntaxe
   ansible-playbook ansible/site.yml --syntax-check

   # Mode verbeux
   ansible-playbook -i inventories/production ansible/site.yml -vvv

Dépannage
---------

Problèmes SSH
~~~~~~~~~~~~~

.. code-block:: bash

   # Tester la connexion SSH
   ssh -i ~/.ssh/id_rsa ubuntu@your-server-ip

   # Vérifier la configuration SSH
   ansible all -i inventories/production -m ping -vvv

Problèmes de permissions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Vérifier les permissions sudo
   ansible all -i inventories/production -m shell -a "sudo whoami" --become

Problèmes Docker
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Vérifier Docker sur l'hôte distant
   ansible all -i inventories/production -m shell -a "docker ps"

Prochaines étapes
-----------------

* Consultez :doc:`docker` pour la configuration Docker
* Configurez la :doc:`security`
* Mettez en place le :doc:`monitoring`
* Configurez les :doc:`backup`

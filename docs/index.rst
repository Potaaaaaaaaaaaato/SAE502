Documentation SAE502 - Déploiement automatisé Django
=====================================================

.. image:: https://img.shields.io/badge/SAE502-Automatisation%20Django-blue?style=for-the-badge
   :alt: SAE502 Badge

.. image:: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
   :alt: Docker

.. image:: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green
   :alt: Django

.. image:: https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white
   :alt: Ansible

Bienvenue
---------

Bienvenue dans la documentation du projet **SAE502** : Automatisation complète du déploiement, 
de la sécurisation et de la supervision d'un site web Django en production.

Ce projet supprime totalement les interventions manuelles de déploiement grâce à :

* **Conteneurisation complète** avec Docker Compose
* **Automatisation du déploiement** avec Ansible
* **Sécurisation** avec HTTPS, fail2ban, UFW
* **Monitoring proactif** avec alertes
* **Backups automatiques** quotidiens
* **CI/CD** avec GitHub Actions

À propos
--------

Ce projet est une solution complète d'automatisation pour déployer une application Django 
en production de manière sécurisée, reproductible et supervisée.

L'objectif principal est de démontrer les bonnes pratiques DevOps modernes :

* Infrastructure as Code (IaC)
* Conteneurisation
* Automatisation complète
* Sécurité par défaut
* Monitoring et alertes

Table des matières
------------------

.. toctree::
   :maxdepth: 2
   :caption: Guide de démarrage

   installation
   architecture

.. toctree::
   :maxdepth: 2
   :caption: Configuration

   docker
   ansible

.. toctree::
   :maxdepth: 2
   :caption: Référence

   api
   security
   monitoring
   backup

Indices et tables
=================

* :ref:`genindex`
* :ref:`search`

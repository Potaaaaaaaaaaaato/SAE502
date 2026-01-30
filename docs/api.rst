Documentation API
=================

Cette page documente les endpoints API de l'application Django SAE502.

Vue d'ensemble
--------------

L'application expose plusieurs endpoints pour :

* **Healthcheck** : Vérification de l'état de l'application
* **API REST** : Endpoints pour les données (optionnel)
* **Admin Django** : Interface d'administration

Endpoints principaux
--------------------

Healthcheck
~~~~~~~~~~~

**Endpoint** : ``/health/``

**Méthode** : ``GET``

**Description** : Vérifie l'état de santé de l'application et de ses dépendances.

**Réponse** :

.. code-block:: json

   {
     "django": "OK",
     "database": "OK",
     "redis": "OK",
     "disk": {
       "usage_percent": 45,
       "healthy": true
     },
     "status": "healthy",
     "timestamp": "2026-01-30T14:00:00Z"
   }

**Codes de statut** :

* ``200 OK`` - Tous les services sont opérationnels
* ``503 Service Unavailable`` - Un ou plusieurs services sont défaillants

**Exemple** :

.. code-block:: bash

   curl http://localhost/health/

Page d'accueil
~~~~~~~~~~~~~~

**Endpoint** : ``/``

**Méthode** : ``GET``

**Description** : Page d'accueil de l'application.

**Réponse** : Page HTML

Page de démonstration
~~~~~~~~~~~~~~~~~~~~~

**Endpoint** : ``/demo/``

**Méthode** : ``GET``

**Description** : Page de démonstration des fonctionnalités.

**Réponse** : Page HTML

Admin Django
~~~~~~~~~~~~

**Endpoint** : ``/admin/``

**Méthode** : ``GET``, ``POST``

**Description** : Interface d'administration Django.

**Authentification** : Requise

**Credentials par défaut** :

* Username: ``admin``
* Password: ``admin123``

.. warning::
   Changez le mot de passe par défaut en production !

API REST (optionnel)
--------------------

Si vous avez configuré Django REST Framework, voici les endpoints disponibles :

Liste des utilisateurs
~~~~~~~~~~~~~~~~~~~~~~~

**Endpoint** : ``/api/users/``

**Méthode** : ``GET``

**Authentification** : Requise (Token)

**Réponse** :

.. code-block:: json

   [
     {
       "id": 1,
       "username": "admin",
       "email": "admin@example.com",
       "first_name": "Admin",
       "last_name": "User"
     }
   ]

Détail d'un utilisateur
~~~~~~~~~~~~~~~~~~~~~~~~

**Endpoint** : ``/api/users/{id}/``

**Méthode** : ``GET``, ``PUT``, ``PATCH``, ``DELETE``

**Authentification** : Requise (Token)

**Réponse** :

.. code-block:: json

   {
     "id": 1,
     "username": "admin",
     "email": "admin@example.com",
     "first_name": "Admin",
     "last_name": "User"
   }

Authentification
----------------

Token Authentication
~~~~~~~~~~~~~~~~~~~~

Pour obtenir un token d'authentification :

**Endpoint** : ``/api/token/``

**Méthode** : ``POST``

**Payload** :

.. code-block:: json

   {
     "username": "admin",
     "password": "admin123"
   }

**Réponse** :

.. code-block:: json

   {
     "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
   }

**Utilisation** :

.. code-block:: bash

   curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
        http://localhost/api/users/

Session Authentication
~~~~~~~~~~~~~~~~~~~~~~

Pour les requêtes depuis le navigateur, utilisez l'authentification par session :

1. Connectez-vous via ``/admin/``
2. Les cookies de session seront automatiquement envoyés

Pagination
----------

Les endpoints de liste supportent la pagination :

**Paramètres** :

* ``page`` - Numéro de page (défaut: 1)
* ``page_size`` - Nombre d'éléments par page (défaut: 10, max: 100)

**Exemple** :

.. code-block:: bash

   curl http://localhost/api/users/?page=2&page_size=20

**Réponse** :

.. code-block:: json

   {
     "count": 45,
     "next": "http://localhost/api/users/?page=3",
     "previous": "http://localhost/api/users/?page=1",
     "results": [...]
   }

Filtrage
--------

Les endpoints supportent le filtrage :

**Paramètres** :

* ``search`` - Recherche textuelle
* ``ordering`` - Tri (préfixe ``-`` pour ordre décroissant)

**Exemple** :

.. code-block:: bash

   # Recherche
   curl http://localhost/api/users/?search=john

   # Tri
   curl http://localhost/api/users/?ordering=-date_joined

Codes de statut HTTP
--------------------

L'API utilise les codes de statut HTTP standards :

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Code
     - Description
   * - ``200 OK``
     - Requête réussie
   * - ``201 Created``
     - Ressource créée avec succès
   * - ``204 No Content``
     - Suppression réussie
   * - ``400 Bad Request``
     - Données invalides
   * - ``401 Unauthorized``
     - Authentification requise
   * - ``403 Forbidden``
     - Permissions insuffisantes
   * - ``404 Not Found``
     - Ressource non trouvée
   * - ``500 Internal Server Error``
     - Erreur serveur
   * - ``503 Service Unavailable``
     - Service temporairement indisponible

Format des erreurs
------------------

Les erreurs sont retournées au format JSON :

.. code-block:: json

   {
     "error": "Resource not found",
     "detail": "User with id 999 does not exist",
     "status_code": 404
   }

Validation des données
~~~~~~~~~~~~~~~~~~~~~~

Les erreurs de validation incluent les champs concernés :

.. code-block:: json

   {
     "username": ["This field is required."],
     "email": ["Enter a valid email address."]
   }

Rate Limiting
-------------

Pour éviter les abus, l'API implémente un rate limiting :

* **Anonyme** : 100 requêtes/heure
* **Authentifié** : 1000 requêtes/heure

**Headers de réponse** :

.. code-block:: http

   X-RateLimit-Limit: 1000
   X-RateLimit-Remaining: 999
   X-RateLimit-Reset: 1643558400

**Dépassement** :

.. code-block:: json

   {
     "error": "Rate limit exceeded",
     "detail": "Too many requests. Try again in 3600 seconds.",
     "status_code": 429
   }

CORS
----

Pour les requêtes cross-origin, configurez CORS dans ``settings.py`` :

.. code-block:: python

   CORS_ALLOWED_ORIGINS = [
       "https://example.com",
       "https://www.example.com",
   ]

   CORS_ALLOW_METHODS = [
       'DELETE',
       'GET',
       'OPTIONS',
       'PATCH',
       'POST',
       'PUT',
   ]

Exemples d'utilisation
-----------------------

Python (requests)
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests

   # Healthcheck
   response = requests.get('http://localhost/health/')
   print(response.json())

   # Authentification
   response = requests.post('http://localhost/api/token/', json={
       'username': 'admin',
       'password': 'admin123'
   })
   token = response.json()['token']

   # Requête authentifiée
   headers = {'Authorization': f'Token {token}'}
   response = requests.get('http://localhost/api/users/', headers=headers)
   print(response.json())

JavaScript (fetch)
~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   // Healthcheck
   fetch('http://localhost/health/')
     .then(response => response.json())
     .then(data => console.log(data));

   // Authentification
   fetch('http://localhost/api/token/', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       username: 'admin',
       password: 'admin123'
     })
   })
   .then(response => response.json())
   .then(data => {
     const token = data.token;
     
     // Requête authentifiée
     return fetch('http://localhost/api/users/', {
       headers: {
         'Authorization': `Token ${token}`
       }
     });
   })
   .then(response => response.json())
   .then(data => console.log(data));

cURL
~~~~

.. code-block:: bash

   # Healthcheck
   curl http://localhost/health/

   # Authentification
   curl -X POST http://localhost/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'

   # Requête authentifiée
   curl http://localhost/api/users/ \
     -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

Webhooks
--------

L'application peut envoyer des webhooks pour certains événements :

Configuration
~~~~~~~~~~~~~

Dans le fichier ``.env`` :

.. code-block:: bash

   WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

Événements
~~~~~~~~~~

* **Service Down** : Un service est indisponible
* **Disk Full** : Espace disque < 10%
* **Backup Failed** : Échec du backup

Format du webhook
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "event": "service_down",
     "service": "postgresql",
     "timestamp": "2026-01-30T14:00:00Z",
     "message": "PostgreSQL is not responding"
   }

Documentation interactive
-------------------------

Pour générer une documentation interactive de l'API, installez ``drf-spectacular`` :

.. code-block:: bash

   pip install drf-spectacular

Accédez ensuite à :

* **Swagger UI** : http://localhost/api/schema/swagger-ui/
* **ReDoc** : http://localhost/api/schema/redoc/
* **OpenAPI Schema** : http://localhost/api/schema/

Prochaines étapes
-----------------

* Consultez :doc:`docker` pour la configuration
* Configurez la :doc:`security`
* Mettez en place le :doc:`monitoring`

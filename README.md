# Tournoi des Moutilloux

Application Django de gestion d’un tournoi de tennis.

Le projet permet de gérer un tournoi avec :

- des joueurs ;
- des équipes ;
- des catégories ;
- des poules ;
- des matchs ;
- des scores ;
- un affichage public des résultats ;
- une interface d’arbitrage ;
- une interface d’administration du tournoi.

---

## Prérequis

Avant d’installer le projet, il faut avoir :

- Python 3.10 ou supérieur ;
- Git ;
- pip ;
- un terminal Linux, macOS ou Windows PowerShell.

---

## Récupérer le projet

Cloner le dépôt GitHub :

```bash
git clone git@github.com:sirius911/moutilloux.git
cd moutilloux
```

---

## Créer l’environnement Python

Créer un environnement virtuel Python dans le dossier `_env` :

```bash
python3 -m venv _env
```

Activer l’environnement virtuel.

### Sous Linux / macOS

```bash
source _env/bin/activate
```

### Sous Windows PowerShell

```powershell
.\_env\Scripts\Activate.ps1
```

Une fois l’environnement activé, le terminal doit afficher quelque chose comme :

```text
(_env)
```

---

## Installer les dépendances Python

Installer les paquets nécessaires :

```bash
pip install -r requirements.txt
```

Si le fichier `requirements.txt` n’existe pas encore, il doit être généré par le développeur du projet avec :

```bash
pip freeze > requirements.txt
```

---

## Configuration de la base de données

Par défaut, le projet utilise une base de données SQLite locale.

La base de données réelle n’est pas fournie dans le dépôt GitHub.  
Elle est reconstruite automatiquement à partir des migrations Django.

Créer les tables de la base de données :

```bash
python manage.py migrate
```

Cette commande crée notamment le fichier local :

```text
db.sqlite3
```

Ce fichier ne doit pas être envoyé sur GitHub.

---

## Créer un compte administrateur

Créer un utilisateur administrateur Django :

```bash
python manage.py createsuperuser
```

Django demande alors :

```text
Username:
Email address:
Password:
Password again:
```

Cet utilisateur permettra d’accéder à l’interface d’administration.

---

## Lancer le serveur de développement

Lancer le serveur Django :

```bash
python manage.py runserver
```

Le site est ensuite accessible à cette adresse :

```text
http://127.0.0.1:8000/
```

L’administration Django est accessible à cette adresse :

```text
http://127.0.0.1:8000/admin/
```

---

## Utilisation sur le réseau local

Pour rendre le site accessible depuis un autre ordinateur, une tablette ou une télévision du même réseau local, lancer le serveur avec :

```bash
python manage.py runserver 0.0.0.0:8000
```

Il faut aussi autoriser l’adresse IP de la machine dans les paramètres Django.

Exemple avec une adresse IP locale :

```bash
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.23 python manage.py runserver 0.0.0.0:8000
```

Le site sera alors accessible depuis une autre machine avec une adresse du type :

```text
http://192.168.1.23:8000/
```

---

## Variables d’environnement utiles

Le projet peut utiliser les variables d’environnement suivantes :

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
```

Exemple en développement :

```bash
export DJANGO_SECRET_KEY="dev-secret-key-change-me"
export DJANGO_DEBUG="True"
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
```

En production ou pour un usage public, il faut utiliser une vraie clé secrète Django et ne pas laisser une valeur de développement.

---

## Fichiers non versionnés

Les fichiers suivants ne sont volontairement pas envoyés sur GitHub :

```text
_env/
db.sqlite3
db.sqlite3-journal
.env
*.log
__pycache__/
```

Cela permet d’éviter de publier :

- l’environnement virtuel Python ;
- la base de données locale ;
- les fichiers temporaires ;
- les éventuels secrets de configuration.

---

## Remettre la base de données à zéro en développement

Supprimer la base locale :

```bash
rm db.sqlite3
```

Recréer la base à partir des migrations :

```bash
python manage.py migrate
```

Recréer un compte administrateur :

```bash
python manage.py createsuperuser
```

---

## Commandes utiles

Lancer les migrations :

```bash
python manage.py migrate
```

Créer de nouvelles migrations après modification des modèles :

```bash
python manage.py makemigrations
```

Recalculer les classements, si nécessaire :

```bash
python manage.py recalc_standings
```

Lancer le serveur :

```bash
python manage.py runserver
```

---

## Structure générale du projet

```text
moutilloux/
├── competition/        # logique de compétition et classements
├── core/               # éléments communs du projet
├── live/               # affichage live, arbitrage, résultats
├── moutilloux/         # configuration principale Django
├── manage.py
├── README.md
└── .gitignore
```

---

## Licence

À définir.
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
- Node.js 20 ou supérieur (avec npm) — pour le front-end de développement ;
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

## Lancer le front-end en développement (SPA Vue 3)

L’interface utilisateur (admin, arbitre, TV) est une SPA **Vue 3 + Vite +
TypeScript** qui vit dans `frontend/app/` et consomme l’API JSON de Django.
En développement, il faut **deux serveurs** qui tournent en même temps.

### 1. Installer les dépendances front (première fois seulement)

```bash
cd frontend/app
npm install
```

### 2. Lancer les deux serveurs

Dans un premier terminal, le back Django (port 8000) :

```bash
source _env/bin/activate
python manage.py runserver
```

Dans un second terminal, le front Vite :

```bash
cd frontend/app
npm run dev
```

L’application est alors accessible sur :

```text
http://localhost:5173/
```

### 3. Comment ça marche

Le serveur Vite **proxifie** `/api`, `/arbitre`, `/panel`, `/accounts` et
`/media` vers `http://localhost:8000` (voir `frontend/app/vite.config.ts`).
Tout passe donc par la même origine : le cookie de session Django et le CSRF
fonctionnent sans configuration supplémentaire.

Routes principales de la SPA :

```text
/login        connexion (session Django)
/tv/live      affichage public TV (scoreboard ⇄ carousel)
/arbitre/…    espace arbitre (tablette) — rôle Arbitre requis
/admin/…      panneau d’administration — superuser requis
```

> Ne pas confondre `/admin/` **de la SPA** (port 5173) avec l’administration
> Django native (`http://127.0.0.1:8000/admin/`), utilisée pour la
> configuration initiale (éditions, catégories, courts).

### 4. Vérification des types

```bash
cd frontend/app
npx vue-tsc -b --force
```

> Utiliser le mode build (`-b --force`) : sur ce projet, `vue-tsc --noEmit`
> seul ne type-check aucun fichier `.vue` (project references non
> déclenchées) et sort en succès silencieux.

Le build de production se fait avec `npm run build` (type-check inclus).

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
├── live/               # affichage live, arbitrage, résultats (API JSON)
├── moutilloux/         # configuration principale Django
├── frontend/
│   ├── app/            # SPA Vue 3 + Vite + TypeScript (admin, arbitre, TV)
│   └── design/         # maquettes de référence (mock React + CSS)
├── specs/              # specs fonctionnelles et techniques (source de vérité)
├── backlog/            # sprints, roadmap, logs de session
├── manage.py
├── README.md
└── .gitignore
```

---

## Licence

À définir.
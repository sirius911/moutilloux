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

Le projet utilise une base de données SQLite locale, **choisie selon
l’environnement** via la variable `MOUTILLOUX_ENV` :

| `MOUTILLOUX_ENV` | Fichier          | Usage                                    |
|------------------|------------------|------------------------------------------|
| `dev` (défaut)   | `db.dev.sqlite3` | Base de travail, jetable                 |
| `prod`           | `db.sqlite3`     | Données réelles du tournoi (jour J)      |

Sans la variable, on est en `dev` : les données réelles ne peuvent pas être
altérées par accident. Les tests (`python manage.py test`) n’utilisent aucun de
ces fichiers — Django crée une base SQLite en mémoire, détruite en fin de run.

La base de données réelle n’est pas fournie dans le dépôt GitHub.  
Elle est reconstruite automatiquement à partir des migrations Django.

Créer les tables de la base de données :

```bash
python manage.py migrate
```

Cette commande crée notamment le fichier local (`db.dev.sqlite3` en dev).

Aucun fichier `*.sqlite3` ne doit être envoyé sur GitHub.

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

> Le compte **arbitre** (utilisateur `arbitre`, mot de passe `arbitre`, membre du
> groupe « Arbitre ») est créé automatiquement par les migrations
> (`live/0026_referee_account`) : rien à faire pour lui. Si le compte existe
> déjà, la migration ne touche pas à son mot de passe. Identifiants triviaux :
> acceptable sur un réseau fermé uniquement.

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

L’administration Django native est accessible à cette adresse :

```text
http://127.0.0.1:8000/django-admin/
```

> `/admin/` est réservé aux écrans d’administration de la SPA Vue : les deux
> partagent le même port dès qu’on sert le build (voir « Utilisation sur le
> réseau local »).

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

> Ne pas confondre `/admin/` **de la SPA** avec l’administration Django native
> (`/django-admin/`), utilisée pour la configuration initiale
> (éditions, catégories, courts).

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

Mode d’emploi pour rendre l’application accessible depuis les autres machines du
réseau (TV, tablettes arbitre, poste admin) — le jour du tournoi, le serveur est
le Mac de l’organisateur.

En réseau local, **on ne lance pas le dev server Vite** : on construit la SPA une
fois et Django la sert lui-même. Un seul process, un seul port, pas de Node au
runtime.

### 1. Construire la SPA

```bash
cd frontend/app && npm ci && npm run build
```

Le build atterrit dans `frontend/app/dist/` (non versionné : à refaire sur la
machine serveur après chaque `git pull`).

### 2. Lancer Django en écoute sur le réseau

Le script `serve_prod.sh` fait tout : il détecte l’adresse IP du Mac et son nom
mDNS, configure `MOUTILLOUX_ENV=prod` (données réelles), `DJANGO_ALLOWED_HOSTS`
et `DJANGO_CSRF_TRUSTED_ORIGINS`, vérifie que le build SPA existe, affiche les
URL à ouvrir sur les autres machines, puis lance le serveur.

```bash
./serve_prod.sh
```

Le port par défaut est 8000 (`./serve_prod.sh 9000` pour en changer).

> macOS n’a pas `hostname -I` : le script détecte l’IP avec
> `ipconfig getifaddr $(route -n get default | awk '/interface:/{print $2}')`
> et le nom mDNS avec `scutil --get LocalHostName`.

À la main, l’équivalent (nécessaire hors macOS) : autoriser l’adresse de la
machine dans `DJANGO_ALLOWED_HOSTS` et la déclarer dans
`DJANGO_CSRF_TRUSTED_ORIGINS` (sinon toutes les écritures — saisie de score,
inscriptions — échouent en 403), et passer `MOUTILLOUX_ENV=prod` pour servir
les données réelles (`db.sqlite3`).

```bash
MOUTILLOUX_ENV=prod \
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.23,moutilloux.local \
DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.23:8000,http://moutilloux.local:8000 \
python manage.py runserver 0.0.0.0:8000
```

### 3. Accéder depuis les autres machines

```text
http://192.168.1.23:8000/tv/live     affichage TV
http://192.168.1.23:8000/arbitre/    tablettes arbitre
http://192.168.1.23:8000/admin/      panneau d’administration (SPA)
http://192.168.1.23:8000/django-admin/   configuration initiale (Django natif)
```

### Points d’attention

- **Adresse IP fixe.** Si le serveur prend une IP différente au prochain
  démarrage, `ALLOWED_HOSTS` ne correspond plus. Réserver une IP dans la box, ou
  utiliser le nom mDNS (`<hostname>.local`), reconnu par macOS et iOS.
- **`DJANGO_DEBUG` reste à `True`.** Le projet n’a pas encore de service de
  fichiers statiques hors DEBUG : avec `DEBUG=False`, les CSS de
  `/django-admin/` ne sont plus servis (les photos et affiches, elles, restent
  servies). Acceptable sur un réseau fermé ; à revoir avant toute exposition
  publique — de même que `DJANGO_SECRET_KEY`, qui doit alors être une vraie clé.
- **`runserver` est un serveur de développement.** Il tient sans problème une TV
  et quelques tablettes en polling ; ce n’est pas un serveur de production.

---

## Variables d’environnement utiles

Le projet peut utiliser les variables d’environnement suivantes :

```text
MOUTILLOUX_ENV
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
```

`MOUTILLOUX_ENV` choisit la base de données (`dev` par défaut → `db.dev.sqlite3` ;
`prod` → `db.sqlite3`, les données réelles). Voir « Base de données ».

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
db.*.sqlite3
db.*.sqlite3-journal
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

Supprimer la base de développement (les données réelles, dans `db.sqlite3`,
ne sont pas concernées) :

```bash
rm db.dev.sqlite3
```

Recréer la base à partir des migrations :

```bash
python manage.py migrate
```

Recréer un compte administrateur (le compte arbitre, lui, est recréé
automatiquement par les migrations) :

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
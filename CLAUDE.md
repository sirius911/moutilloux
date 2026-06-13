# CLAUDE.md — Moutilloux (couche front-end Vue 3)

Ce fichier est le socle de conventions partagé par la session principale (orchestrateur)
et par tous les subagents. Tout agent doit le respecter sans qu'on ait à le répéter.

## 1. Contexte

Moutilloux est une application Django de gestion d'un tournoi de tennis.
Le backend est **quasi complet** : moteur de score, classements auto-recalculés,
qualification + génération de bracket + progression des gagnants, rôle Arbitre + permissions.

Le travail à faire est **front-end** (une SPA Vue 3 qui consomme l'API JSON Django et
reproduit l'UX pixel-perfect du dossier `frontend/design/`) **plus une connectique API légère**
(exposer en JSON propre des mutations dont la logique existe déjà dans `live/admin_views.py`).

On NE réécrit AUCUNE logique métier. On expose et on branche.

**État du front (`frontend/app/`) — déjà échafaudé.** Le projet Vite/Vue/TS existe avec :
- composables `useApi.ts` (CSRF + session), `usePolling.ts`, `useScale.ts` ;
- stores Pinia `auth`, `event`, `live` ; router (`/login`, `/tv/*` public, `/arbitre/*`, `/admin/*`) ;
- ≈20 SFC (admin, arbitre, tv, modales) avec le CSS du design porté ;
- `vuedraggable` installé (drag-and-drop P3/P7).

Les **lectures** et l'**auth** sont branchées sur l'API réelle ; plusieurs **appels de mutation
sont encore spéculatifs** (mauvaises routes/champs) et seront recâblés vers les endpoints `/api/`
au fil des phases. La source de vérité des contrats reste `live/admin_views.py`, pas le front.

**Lancement (dev).** Deux serveurs : `python manage.py runserver` (:8000) et, dans `frontend/app/`,
`npm run dev`. Le proxy Vite renvoie `/api`, `/arbitre`, `/panel`, `/accounts` vers :8000
(même origine → cookie de session + CSRF OK).

## 2. Stack et décisions (validées, non négociables)

| Choix              | Décision                                                                 |
|--------------------|--------------------------------------------------------------------------|
| Front              | Vue 3 + Vite + TypeScript + Vue Router + Pinia                           |
| Inspiration UI     | Le React `frontend/design/` (mock) — CSS réutilisé tel quel, JSX porté en SFC `.vue` |
| Temps réel         | Polling HTTP, pas de WebSockets — code actuel 300 ms ; cible ~2 s (live) / ~4 s (TV) à appliquer |
| Config initiale    | Éditions / catégories / courts via l'admin Django (`/admin/`), pas d'UI dédiée |
| Séquencement       | Phases dans l'ordre 1 → 8                                                 |

## 3. Règles d'orchestration

**L'unité d'orchestration est la phase, pas la roadmap.**
On construit une phase, on la vérifie (golden path), puis seulement on passe à la suivante.
Ne jamais enchaîner plusieurs phases dans un run non interruptible : les portes de
vérification end-to-end par phase sont des points de contrôle humains.

**Le parallélisme vit À L'INTÉRIEUR d'une phase, pas entre les phases.**
La roadmap est une chaîne de dépendances (`0 → 2 → 3 → 4 → 5 → 6 → 7 → 8`, P1 en branche
indépendante depuis P0). Fan-out autorisé seulement quand les tâches touchent des fichiers
disjoints :
- **front ∥ back** sur un contrat d'API convenu d'avance (voir `roadmap/`) ;
- **multi-écrans** quand une phase a plusieurs écrans indépendants (typiquement P5 :
  Arbitre Home, Arbitre Score, Scoreboard TV).

**Les subagents ne se parlent pas entre eux.** Ils ne remontent qu'à l'orchestrateur.
Donc :
- chaque subagent ne crée/édite QUE ses propres fichiers (sa SFC, sa fonction de service) ;
- **l'orchestrateur (session principale) fait lui-même le câblage des fichiers partagés**
  une fois les agents revenus.

**Fichiers partagés / de contention — réservés à l'orchestrateur :**
- Front : `frontend/app/src/router/`, les stores Pinia (`auth`/`event`/`live`),
  `src/composables/useApi.ts`, `src/composables/usePolling.ts`, `src/main.ts`
- Back : `live/urls.py`, et les fonctions de service mutualisées dans `live/admin_views.py`

**Routage par modèle (à régler côté session, pas dans les agents) :**
- Opus pour l'orchestrateur et les blocs lourds (Sprint 0, Phase 5).
- Modèle plus léger pour les phases S read-only (P1, P6, P8).
Les subagents `vue-screen` et `django-api` héritent du modèle de session (`model: inherit`).

## 4. Conventions front (Vue 3 + TS)

- **Une SFC `.vue` par écran**, portée depuis le `.jsx` de référence cité dans le prompt.
  Reproduire la structure et le comportement, pas réinventer.
- **CSS** : importer et réutiliser tel quel les fichiers de `frontend/design/`
  (`tokens.css`, `app.css`, `scoreboard.css`, `arbitre.css`, `spectator.css`, `admin.css`,
  `modals.css`). Ne pas réécrire de styles — `tokens.css` est la source de vérité visuelle.
- **Données** : tout passe par le composable `useApi()` (`src/composables/useApi.ts`, expose
  `get/post/patch`) — jamais de `fetch` brut dans une SFC.
  L'état partagé vit dans les stores Pinia (`auth`, `event`, `live`).
- **Temps réel** : utiliser le composable `usePolling(fetcher, intervalMs)`.
  État actuel du code : 300 ms (arbitre + scoreboard). Cible visée ~2 s arbitre/scoreboard,
  ~4 s poules/bracket TV — **non encore appliquée**. Pause si onglet caché : **non implémentée**
  dans `usePolling` (TODO).
- **Rôles / routing** : cible = Admin → garde `isAdmin` ; Arbitre → garde `isReferee` ;
  Spectateur (TV) → public. **État actuel** : `router/index.ts` vérifie `requiresAuth` et
  `requiresAdmin` (garde `isAdmin` en place sur `/admin/*`) ; la garde `isReferee` sur
  `/arbitre/*` manque encore (backlog 023).
- **CSRF/session** : POST via `useApi` qui lit le cookie CSRF (`csrftoken`) et envoie
  `X-CSRFToken`, avec `credentials:'include'`. En dev, tout passe par le proxy Vite (même origine).
  Note : `useApi` `throw` sur tout statut non-2xx ; la **redirection sur 401 n'est pas encore
  gérée** (TODO).
- **TypeScript** : typer les payloads d'après le contrat de la phase (`roadmap/`).
  `types/index.ts` contient déjà un jeu de types riche, cohérent avec `_pack_match`.
- **Définition de terminé** : le type-check passe (`npx vue-tsc --noEmit` ; script `type-check`
  à ajouter dans `package.json`) et l'écran rend correctement sur sa cible
  (desktop admin / iPad arbitre / TV 1080p).

## 5. Conventions back (connectique API)

- **Ne pas dupliquer la logique.** Extraire le cœur d'une mutation de `admin_views.py`
  en **fonction de service réutilisable**, puis exposer un **endpoint `/api/` JSON fin**
  par-dessus. La vue template existante doit appeler la même fonction de service.
- Endpoints en **JSON** des deux côtés (requête JSON, réponse JSON), auth par session.
- Réutiliser le packer `_pack_match` (`api_views.py:97`) pour toute réponse décrivant un match.
- **Ne pas câbler `live/urls.py` soi-même** : un agent rend la vue + la fonction de service,
  l'orchestrateur ajoute la route.
- Respecter le contrat de la phase dans `roadmap/` ; si un champ y est marqué
  « à confirmer », le lire dans le code source et mettre le contrat à jour.

## 6. Vérification (golden path, par phase)

Avant de clore une phase : lancer le scénario de vérification décrit dans la roadmap pour
cette phase (création, mutation, lecture, recalcul auto), sur les 3 cibles d'écran le cas échéant.
Une action invalide (ex. changer le service en cours de jeu) doit renvoyer l'erreur JSON
attendue et l'UI doit l'afficher.

## 7. Subagents disponibles

- `vue-screen` — porte un écran `.jsx` de `design/` en SFC `.vue`.
- `django-api` — extrait une mutation en service + expose un endpoint `/api/` JSON.
- `reviewer` — œil neuf, lecture seule : relit une livraison contre la réf design + le contrat.

Garder ce roster petit. Ne pas multiplier les agents spécialisés.

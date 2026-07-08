---
type: technical
module: affiche-match
fichiers:
  - scripts/generate_match_poster.py
  - scripts/README.md
  - core/models.py
  - live/models.py
  - live/admin_views.py
  - live/api_views.py
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
---

# Spec technique — Affiches de match (génération IA)

> Intégration du prototype `generate_match_poster` (PR #1, branche
> `generate_match_poster`, commit `6db535a`) dans l'application : une affiche
> « jeu de combat arcade » générée par l'API OpenAI Images à partir des photos
> des joueurs, **choisie côté admin**, **stockée sur le match**, **affichée par
> la TV**. Issu du brainstorm produit du 2026-07-04.

## Principe

- **La TV n'affiche que le résultat** : le match porte son affiche retenue
  (`Match.poster`), exposée par `_pack_match` — aucune logique de génération
  côté public.
- **Tout le reste est admin** : upload des photos (fiche joueur), génération
  (2 propositions par lot, asynchrone), choix de l'élue, retrait.
- **La PR #1 est la base de travail** : le sprint porteur **rebase le commit
  `6db535a`** sur sa branche, puis en extrait le cœur (construction du prompt,
  appel API) en module importable — le CLI `scripts/` reste utilisable tel
  quel pour les essais.

---

## Modèles (à créer / étendre)

| Champ / modèle | Type | Rôle |
|---|---|---|
| `Player.photo` | ImageField (optionnel, `media/players/`) | portrait du joueur, source des affiches (et de l'avatar admin) |
| `Player.attitudes` | JSONField (liste de chaînes, défaut `[]`) | adjectifs d'attitude du joueur, choisis parmi la **liste prédéfinie** (constantes front `frontend/app/src/constants/attitudes.json`, voir [[admin-joueurs]]) ; le serveur stocke les valeurs sans les re-valider contre la liste. Pas de migration de données (aucune donnée de prod) — migration de schéma simple depuis l'ancien `attitude` CharField. |
| `Match.poster` | ImageField (optionnel, `media/match_posters/`) | l'affiche **retenue** du match |
| `PosterJob` | modèle | une génération en cours/finie pour un match |

**`PosterJob`** : `match` (FK), `status` (`PENDING` / `RUNNING` / `DONE` /
`ERROR`), `error` (texte), `attitudes` (JSON — les valeurs utilisées),
`created_at`. Les **2 candidates** produites sont rattachées au job (fichiers
`media/match_posters/candidates/`). Un seul job actif par match (relancer
remplace le job précédent et purge ses candidates).

**Cycle de vie des candidates** : elles n'existent que le temps du choix.
**Choisir** une candidate → elle devient `Match.poster`, le job et **toutes**
les candidates sont purgés (décision : on ne garde que l'élue). **Relancer**
avant choix → nouveau lot de 2, l'ancien est purgé. **Retirer l'affiche** →
`Match.poster` effacé (fichier supprimé).

## Pipeline de génération (asynchrone + polling)

1. `POST /api/matches/<id>/poster/generate/` (superuser) — body
   `{attitudes: {A: "...", B: "..."} }` (un adjectif par side). Le formulaire de
   l'onglet Affiche pré-remplit chaque champ par **tirage au sort** parmi les
   `Player.attitudes` du joueur (vide s'il n'en a aucune) ; l'admin peut
   remplacer ce tirage par un choix explicite (sélecteur parmi les attitudes du
   joueur, ou la liste prédéfinie complète) avant de lancer. **Gardes** : les deux sides résolus, photo présente sur
   **chaque** joueur concerné (en Double : les 4), clé API configurée, pas de
   job déjà `RUNNING`. Refus 400 avec message explicite sinon.
2. Le serveur crée le `PosterJob` (`PENDING`) et lance la génération **dans un
   thread** (pas de Celery dans le projet) : construction du prompt (module
   extrait du script — mêmes contraintes : titre seul texte autorisé, zone
   basse 25-30 % réservée au score, adjectifs jamais écrits), appel
   `images.edit` (n=2, 1536×1024, quality medium), écriture des candidates,
   `DONE` (ou `ERROR` + message).
3. Le front **polle** `GET /api/matches/<id>/poster/` (~2 s pendant un job) :
   `{ posterUrl, job: {status, error, candidates: [urls]} | null }`.
4. `POST /api/matches/<id>/poster/select/` — body `{candidate}` → copie vers
   `Match.poster`, purge du job. `POST /api/matches/<id>/poster/clear/` →
   retire l'affiche.

Conventions back (CLAUDE.md §5) : la logique vit en **module/service**
(`live/posters.py` : prompt + appel API + job runner), les endpoints sont
fins ; `live/urls.py` est câblé par l'orchestrateur. Le module est **partagé**
avec le CLI `scripts/generate_match_poster.py` (une seule construction de
prompt, pas deux).

## Contrat `_pack_match`

- Nouveau champ **`posterUrl`** (`/media/match_posters/…` ou `null`) dans
  `_pack_match` — il irrigue automatiquement l'admin, `tv/state` (hero) et
  `tv/idle` (programme → l'affiche du prochain match pour la slide dédiée).

## Photos des joueurs

- Upload dans la **modale Fiche joueur** ([[admin-joueurs]]) : jpg/jpeg/png/webp,
  ≤ 10 Mo, aperçu dans la modale ; l'avatar à initiales reste le repli partout
  où la photo manque.
- Endpoint d'upload dédié (`POST /api/players/<id>/photo/`, multipart,
  superuser) — les autres champs restent en JSON.
- Consentement : les photos partent vers l'API OpenAI à la génération — à
  l'appréciation de l'organisateur (tournoi privé), noté ici pour mémoire.

## Dépendances & configuration

- **Isoler les dépendances du prototype** : ne PAS fusionner le freeze de la
  PR #1 dans `requirements.txt` — ajouter uniquement `openai` (et `pillow`
  pour ImageField) au projet ; le reste (dotenv, requests) n'est utile qu'au
  CLI (`scripts/requirements.txt` dédié).
- `OPENAI_API_KEY` en variable d'environnement serveur (`.env` non versionné,
  déjà ignoré). Sans clé : la génération est refusée avec un message clair,
  tout le reste de l'app fonctionne.
- Coûts : ~2 images/lot, quality `medium`, relance manuelle — pas de
  génération automatique en masse (hors périmètre).

## Affichage TV (voir [[tv-live]])

- **Scoreboard LIVE** : si `hero.posterUrl` existe, l'affiche remplace le fond
  de court ; la zone d'enjeu (classement de poule) s'affiche **par-dessus**
  en panneau semi-transparent, la bande de score occupe la zone basse réservée
  par le visuel. Sans affiche : fond actuel.
- **Slide « Affiche »** du carousel : l'affiche du **prochain match** quand
  elle existe (~heure + « à l'affiche »), sinon slide sautée.

## Hors périmètre

- Génération automatique (batch de tous les matchs) ; programmation.
- Le score incrusté **dans** l'image (le score reste du HTML par-dessus).
- Historique / galerie des affiches passées (une affiche par match, point).
- Choix du modèle/qualité depuis l'UI (constantes serveur).

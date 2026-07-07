---
sprint: 24
nom: "Affiches de match"
specs:
  - specs/technical/affiche-match.md
  - specs/screens/admin-joueurs.md
  - specs/screens/admin-matchs.md
  - specs/screens/tv-live.md
modules:
  - scripts/generate_match_poster.py
  - core/models.py
  - live/models.py
  - live/posters.py
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
  - moutilloux/settings.py
  - moutilloux/urls.py
  - frontend/app/vite.config.ts
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/views/admin/AdminPlayers.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
tickets-tag: sprint-24
branche: claude/sprint/24-affiches-match
branche-parent: main
log: backlog/sprints/24-affiches-match/log.md
---

# Sprint 24 — Affiches de match

**Objectif :** Intégrer le prototype de la **PR #1** (affiches IA « jeu de
combat » générées depuis les photos des joueurs) dans l'application, selon
`affiche-match.md` : photos et attitudes sur la **fiche joueur**, génération
**asynchrone** et choix depuis l'**onglet Affiche** du panneau de match,
affiche stockée sur le match (`posterUrl` de `_pack_match`), affichée par la
TV (fond du scoreboard LIVE + slide du carousel).

> Origine : PR #1 (`generate_match_poster`, commit `6db535a`, contributeur
> ArtSkamos) + brainstorm produit du 2026-07-04. **Prérequis : sprint 23**
> (TvScoreboard/TvIdle rebranchés sur tv-state — les deux tickets TV s'y
> greffent) et **sprint 17** (panneau d'édition remanié — l'onglet s'y
> ajoute). **Setup de branche particulier** : la branche du sprint
> **cherry-pick `6db535a`** avant tout (ticket #263) ; la **PR #1 sera fermée
> « intégrée par le sprint 24 »** à la clôture du sprint.

## Définition de terminé

- **Golden path complet :** photo + attitude sur deux fiches joueurs → ouvrir
  leur match (onglet Affiche, ou raccourci ligne) → « Générer 2
  propositions » → suivi de progression → choisir une candidate → l'affiche
  apparaît dans l'onglet, `posterUrl` est servi ; démarrer le match → la TV
  l'affiche en fond du scoreboard, l'enjeu par-dessus reste lisible, le score
  en bande basse.
- **Golden path candidates :** relancer avant choix → jamais plus de 2
  fichiers candidats ; choisir → job et candidates purgés, seule l'élue
  demeure ; « Retirer » efface l'affiche (fichier compris).
- **Golden path gardes :** génération refusée avec message explicite si photo
  manquante (nom du joueur cité), sides non résolus, clé API absente, job en
  cours. Sans `OPENAI_API_KEY`, tout le reste de l'app fonctionne.
- **Golden path TV idle :** le prochain match a une affiche → la slide
  « Affiche » entre en rotation ; sinon elle est sautée.
- Dépendances isolées : `requirements.txt` projet n'ajoute que `openai` +
  `pillow` ; le CLI garde son `scripts/requirements.txt`.
- Spec review `✅ Conforme` sur `affiche-match.md` (et sections amendées
  d'`admin-joueurs` / `admin-matchs` / `tv-live`).
- Aucune issue `sprint-24` ouverte (hors `en-attente`) ; **PR #1 fermée**.

## Specs ciblées

- [`specs/technical/affiche-match.md`](../../../specs/technical/affiche-match.md) — modèles, pipeline asynchrone, contrat, dépendances
- [`specs/screens/admin-joueurs.md`](../../../specs/screens/admin-joueurs.md) — photo + attitude sur la fiche
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — onglet Affiche + raccourci ligne
- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — fond de scène + slide Affiche

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 24 — Affiches de match »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#263](https://github.com/sirius911/moutilloux/issues/263) | Intégrer la PR #1 (cherry-pick 6db535a) + isoler les dépendances | `scripts/`, `requirements.txt` | `infra` — **premier geste**, orchestrateur |
| [#264](https://github.com/sirius911/moutilloux/issues/264) | Modèles photo/attitude/poster/PosterJob + config média | `core/models.py`, `live/models.py`, `settings.py`, `urls.py`, `vite.config.ts` | `infra` — débloque tout |
| [#265](https://github.com/sirius911/moutilloux/issues/265) | Module `live/posters.py` (prompt partagé + job asynchrone) | `live/posters.py`, `scripts/` | Dépend de #263 + #264 |
| [#266](https://github.com/sirius911/moutilloux/issues/266) | Endpoints `/api/matches/<id>/poster/*` | `api_views.py`, `urls.py` | `infra` ; dépend de #265 |
| [#268](https://github.com/sirius911/moutilloux/issues/268) | Upload photo joueur (multipart) + photoUrl | `api_views.py`, `urls.py` | `infra` ; dépend de #264 |
| [#270](https://github.com/sirius911/moutilloux/issues/270) | Onglet « Affiche » d'EditMatchPanel + raccourci ligne | `EditMatchPanel.vue`, `AdminMatches.vue` | Dépend de #266 + #267 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#267](https://github.com/sirius911/moutilloux/issues/267) | `posterUrl` dans `_pack_match` + type Match | `api_views.py`, `types/index.ts` | Dépend de #264 |
| [#269](https://github.com/sirius911/moutilloux/issues/269) | Fiche joueur : photo (aperçu) + attitude ; avatar registre | `AddPlayerModal.vue`, `AdminPlayers.vue` | Dépend de #268 |
| [#271](https://github.com/sirius911/moutilloux/issues/271) | TV : affiche en fond du scoreboard LIVE | `TvScoreboard.vue` | Dépend de #267 + sprint 23 |
| [#272](https://github.com/sirius911/moutilloux/issues/272) | TV : slide « Affiche » du carousel | `TvIdle.vue` | Dépend de #267 + sprint 23 |

---

## Périmètre backend

- **#263** — cherry-pick + assainissement des dépendances (voir issue).
- **#264** — migrations core+live, `MEDIA_ROOT`/`MEDIA_URL` + serving dev.
- **#265** — cœur métier : prompt extrait du script (une seule vérité),
  runner thread, cycle de vie PosterJob (purge stricte des candidates).
- **#266/#268** — endpoints fins superuser ; l'upload photo est le seul
  endpoint **multipart** du projet.
- **#267** — `posterUrl` dans `_pack_match` (irrigue admin + TV sans autre
  packer).

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` — routes poster/* (#266) et photo (#268).
- `moutilloux/settings.py`, `moutilloux/urls.py`, `frontend/app/vite.config.ts`
  — config média (#264).
- `requirements.txt` — #263.
- **Contention** : `api_views.py` touché par #266, #267, #268 (blocs
  distincts, séquencer) ; `EditMatchPanel.vue` par #270 seul ;
  `AdminMatches.vue` par #270 (raccourci — léger).

## Ordre d'exécution suggéré

1. **#263** — cherry-pick + dépendances (orchestrateur, avant tout).
2. **#264** — modèles + config média (débloque tout le reste).
3. **#265** ∥ **#268** — le job de génération et l'upload photo (fichiers
   disjoints hors `urls.py`).
4. **#266** ∥ **#267** — endpoints poster + posterUrl (petits, après #265).
5. **#269** ∥ **#270** — les deux fronts admin en parallèle (fichiers
   disjoints).
6. **#271** ∥ **#272** — les deux fronts TV en parallèle, en dernier
   (s'appuient sur le TvScoreboard/TvIdle du sprint 23).

**Parallélisme :** back d'abord (#263 → #264 → #265 ∥ #268 → #266 ∥ #267),
puis deux paires de fronts parallèles.

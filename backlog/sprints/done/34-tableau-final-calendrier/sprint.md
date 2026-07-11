---
sprint: 34
nom: "Tableau final au calendrier"
specs:
  - specs/technical/planning.md
  - specs/screens/admin-matchs.md
  - specs/technical/cycle-de-vie-match.md
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - live/api_views.py
  - live/referee_views.py
  - live/admin_views.py
  - frontend/app/src/views/admin/AdminMatches.vue
tickets-tag: sprint-34
branche: claude/sprint/34-tableau-final-calendrier
branche-parent: main
log: backlog/sprints/34-tableau-final-calendrier/log.md
---

# Sprint 34 — Tableau final au calendrier

**Objectif :** faire entrer les matchs de tableau (QF/SF/F/P3) dans le circuit
calendrier — pile « à planifier » dès « Débuter », étiquettes de provenance,
garde de démarrage sur slots non résolus, durées ETA par étape — et lever ainsi
le blocage structurel : aujourd'hui **aucun chemin UI ne permet de planifier ni
de lancer un match de phase finale**.

> Origine : retours produit 2026-07-08 (problématique 5) — levée du
> « hors périmètre Phase 2 » historique de [[planning]]. Le squelette naît déjà
> `SCHEDULED` sans `order_index` avec ses étiquettes (`live/bracket.py`) ; le
> reorder écrit déjà `scheduled_time` ; `get_tv_next`, le programme arbitre et
> la ponctualité sont déjà agnostiques au stage. L'essentiel du sprint est le
> **retrait d'un filtre** + l'affichage. Embarque aussi le résidu de #307
> (`.play-day` clippé).

## Définition de terminé

- Golden path : « Débuter » une épreuve à 2 poules → la pile montre les matchs
  de poule **et** les matchs de tableau étiquetés (« A1 vs B2 », groupe
  « Tableau ») ; glisser la finale dans une journée → ETA calculée avec la
  durée longue ; tenter de la démarrer (arbitre) ou de la mettre à l'antenne
  (admin) → **erreur JSON affichée**, match toujours PRÉVU ; terminer les
  poules → slots résolus, noms affichés, le match se démarre et apparaît en
  « À suivre » / programme TV.
- Les cartes de journée ne clippent plus leur contenu (scroll fluide, coins
  arrondis intacts).
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[planning]] (§ Matchs de tableau au
  calendrier) et [[admin-matchs]].
- Aucune issue `sprint-34` ouverte.

## Specs ciblées

- [`specs/technical/planning.md`](../../../specs/technical/planning.md) — § Matchs de tableau au calendrier, durées par étape
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — pile tous stages, étiquettes, anti-clipping `.play-day`
- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — garde « slot non résolu » sur démarrer
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) — « Débuter » alimente la pile (squelette)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 34 — Tableau final au calendrier »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#323](https://github.com/sirius911/moutilloux/issues/323) | Back : pile « à planifier » et Annulés tous stages (retrait filtre GROUP) | `live/api_views.py` | débloque #325 |
| [#324](https://github.com/sirius911/moutilloux/issues/324) | Back : garde « slot non résolu » sur démarrer / mettre à l'antenne | `live/referee_views.py`, `live/admin_views.py` | `infra` — service partagé |
| [#325](https://github.com/sirius911/moutilloux/issues/325) | Front : AdminMatches — pile tous stages (groupe Tableau, pastilles, étiquettes) | `AdminMatches.vue` | dépend de #323 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#326](https://github.com/sirius911/moutilloux/issues/326) | Front : moteur ETA — durée par étape | `AdminMatches.vue` | même fichier que #325 |
| [#327](https://github.com/sirius911/moutilloux/issues/327) | Front : règle de repos best-effort sur slots non résolus | `AdminMatches.vue` | même fichier que #325 |
| [#328](https://github.com/sirius911/moutilloux/issues/328) | Front (résidu #307) : `.play-day` — retirer overflow:hidden | `AdminMatches.vue` | même fichier que #325 |

---

## Périmètre backend

Deux briques indépendantes : le retrait du filtre `stage=GROUP` du packer
calendrier (#323, lecture seule) et la garde de démarrage dans le **service
partagé** arbitre/admin (#324 — une seule vérité, deux surfaces, CLAUDE.md §5).

## Fichiers partagés (orchestrateur uniquement)

- `live/admin_views.py` (service de démarrage mutualisé, #324) — l'orchestrateur
  câble ; pas de nouvelle route attendue (`live/urls.py` intact a priori).

## Ordre d'exécution suggéré

1. #323 (back, débloque le front) ∥ #324 (back, indépendant).
2. Puis #325 → #326 → #327 → #328 **séquentiels** (tous dans
   `AdminMatches.vue` — un seul agent `vue-screen` les enchaîne, pas de
   parallélisme intra-fichier).

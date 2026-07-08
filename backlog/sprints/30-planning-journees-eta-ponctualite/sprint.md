---
sprint: 30
nom: "Planning : journées, ETA monotone & ponctualité"
specs:
  - specs/technical/planning.md
  - specs/screens/admin-matchs.md
modules:
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/PlayDayModal.vue
tickets-tag: sprint-30
branche: claude/sprint/30-planning-journees-eta-ponctualite
branche-parent: main
log: backlog/sprints/30-planning-journees-eta-ponctualite/log.md
---

# Sprint 30 — Planning : journées, ETA monotone & ponctualité

**Objectif :** aligner le Calendrier sur les décisions 31-32 : génération des
journées depuis les dates de l'édition (9:00 → 20:00 par défaut), moteur d'ETA
réécrit avec **curseur monotone** (un match fini en avance ne tire plus
l'aval), indicateur de ponctualité rouge/orange/vert (tolérance 5 min), heure
de début de journée éditable en place — et le bug de scroll des journées.

> Origine : revue produit 2026-07-07 (page Planning, 5 retours + 1 bug). La
> décision 18 (heures dérivées, jamais saisies) est **réaffirmée** : pas
> d'heure par match.

## Définition de terminé

- Golden path génération : édition datée du 25 au 28 avec une journée déjà
  créée le 26 → « Générer depuis l'édition » propose 25/27/28 (9:00-20:00),
  crée 3 journées ; relancer → rien à créer.
- Golden path ETA : durée 30 min, journée à 9:00 — match 1 fini à 9:10 → le
  suivant reste ~9:30 ; fini à 9:50 → le suivant passe ~9:50 (stable au
  rechargement de page).
- Golden path ponctualité : match planifié ~9:30 non démarré à 9:36 → ligne
  rouge ; démarré à 9:38 → orange ; démarré à 9:31 → vert.
- Le calendrier défile (molette/trackpad) sur 3 journées de 8 matchs.
- Spec review `✅ Conforme` sur [[planning]] et [[admin-matchs]].
- Aucune issue `sprint-30` ouverte.

## Specs ciblées

- [`specs/technical/planning.md`](../../../specs/technical/planning.md) — algorithme ETA monotone, indicateur de ponctualité, `play-days/generate/`
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — modale Gérer les journées, en-tête de journée, teintes, légende

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 30 — Planning : journées, ETA monotone & ponctualité »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#302](https://github.com/sirius911/moutilloux/issues/302) | Back : service + endpoint play-days/generate/ | `live/admin_views.py`, `live/api_views.py`, `live/urls.py` | `infra` — câblage urls.py par l'orchestrateur |
| [#303](https://github.com/sirius911/moutilloux/issues/303) | Front : PlayDayModal — « Générer depuis l'édition » | `PlayDayModal.vue` | dépend de #302 |
| [#304](https://github.com/sirius911/moutilloux/issues/304) | Front : moteur ETA — curseur monotone | `AdminMatches.vue` | **avant** #305 |
| [#305](https://github.com/sirius911/moutilloux/issues/305) | Front : teinte de ponctualité + légende | `AdminMatches.vue` | dépend de #304 |
| [#307](https://github.com/sirius911/moutilloux/issues/307) | Front (bug) : impossible de scroller dans les journées | `AdminMatches.vue` | indépendant, peut passer en premier |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#306](https://github.com/sirius911/moutilloux/issues/306) | Front : heure de début de journée éditable en place | `AdminMatches.vue` | réutilise `play-days/<id>/edit/` |

---

## Périmètre backend

`generate_play_days(edition, start_time, target_end_time)` (service idempotent
+ endpoint). Aucune migration.

## Fichiers partagés (orchestrateur uniquement)

`live/urls.py` (route `play-days/generate/`) — câblé par l'orchestrateur (#302).

## Ordre d'exécution suggéré

1. #302 (back) ∥ #307 (bug scroll, CSS isolé).
2. #303 (modale) après #302.
3. #304 → #305 → #306 (même SFC `AdminMatches.vue`, séquentiel — #304 d'abord,
   les teintes de #305 se calculent sur ses ETA).

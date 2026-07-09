---
sprint: 36
nom: "Échauffement"
specs:
  - specs/technical/cycle-de-vie-match.md
  - specs/screens/arbitre-match.md
  - specs/screens/tv-live.md
  - specs/technical/tv-state.md
modules:
  - live/models.py
  - live/api_views.py
  - live/referee_views.py
  - live/admin_views.py
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/types/index.ts
tickets-tag: sprint-36
branche: claude/sprint/36-echauffement
branche-parent: main
log: backlog/sprints/36-echauffement/log.md
---

# Sprint 36 — Échauffement

**Objectif :** insérer la phase d'**échauffement** entre « Démarrer » et le
choix du serveur : `LIVE` + deux horodatages (`warmup_started_at` /
`play_started_at`, pas de nouveau statut), compte à rebours 5 min (constante,
indicatif) synchronisé tablette/TV, scoring refusé tant que le match n'est pas
lancé, et la scène TV « affiche plein écran » pendant l'échauffement.

> Origine : retours produit 2026-07-08 (problématique 4). Fait évoluer le flux
> « premier serveur » du sprint 32 (le choix du serveur ne se fait plus au
> Démarrer mais au lancement) et réutilise la mécanique de scènes TV du
> sprint 35. `started_at` reste posé par `mark_live` — les ETA et la
> ponctualité mesurent l'occupation du court dès l'échauffement, sans
> changement.

## Définition de terminé

- Golden path : « Démarrer » (confirmation seulement si un autre match est en
  cours) → badge ÉCHAUFFEMENT + compte à rebours sur la tablette, affiche
  plein écran + même compte à rebours sur la TV ; taper une zone → toast
  d'erreur du moteur ; « Lancer le match » → modal serveur (aucun
  présélectionné) → confirmer avec B → zones actives, ● côté B, la TV bascule
  sur le scoreboard ; à 0:00 sans lancement → libellé « prêt » / « Le match va
  commencer », rien d'automatique.
- Reprise : mettre le match en pause (démarrer un autre) puis le redémarrer →
  retour **direct en jeu** (pas de ré-échauffement) ; mise à l'antenne admin
  d'un match jamais lancé → échauffement.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[cycle-de-vie-match]] (§ Les deux phases de
  LIVE), [[arbitre-match]] (modes + flux) et [[tv-live]] (état ÉCHAUFFEMENT).
- Aucune issue `sprint-36` ouverte.

## Specs ciblées

- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — phases de LIVE, transitions, gardes
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — quatre modes, flux démarrer / lancer
- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — état ÉCHAUFFEMENT
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) — `warmupStartedAt`/`playStartedAt` dans le contrat

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 36 — Échauffement »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#333](https://github.com/sirius911/moutilloux/issues/333) | Back : champs warmup/play_started_at + mark_live + _pack_match | `live/models.py`, `live/api_views.py` | débloque tout |
| [#334](https://github.com/sirius911/moutilloux/issues/334) | Back : action « lancer le jeu » + refus du scoring en échauffement | `live/referee_views.py`, `live/admin_views.py` | `infra` — service partagé ; dépend de #333 |
| [#335](https://github.com/sirius911/moutilloux/issues/335) | Front : ArbitreMatch — mode échauffement (compte à rebours + Lancer) | `ArbitreMatch.vue`, `types/index.ts` | `infra` — types partagés ; dépend de #333/#334 |
| [#336](https://github.com/sirius911/moutilloux/issues/336) | Front : TvScoreboard — scène ÉCHAUFFEMENT | `TvScoreboard.vue` | dépend de #333 (+ types posés via #335) |

---

## Périmètre backend

Une migration (2 DateTime nullables) + l'évolution du couple
`mark_live`/`referee_action` : `start` sans serveur, nouvelle action de
lancement (service partagé arbitre/admin, CLAUDE.md §5), refus des actions de
scoring en phase d'échauffement.

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/types/index.ts` (`Match` += `warmupStartedAt`/
  `playStartedAt`) — à poser par l'orchestrateur **en tête de sprint** (les
  deux SFC en dépendent).
- `live/admin_views.py` / `live/urls.py` si l'action de lancement passe par une
  nouvelle route (à défaut, réutiliser le canal `action` existant de
  `/arbitre/match/<id>/action/`).

## Ordre d'exécution suggéré

1. #333 (migration + packers) — débloque tout.
2. #334 (back, actions) ; en parallèle l'orchestrateur pose les types partagés.
3. #335 ∥ #336 (deux SFC disjointes, deux `vue-screen` en parallèle).

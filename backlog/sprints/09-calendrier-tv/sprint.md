---
sprint: 9
nom: Calendrier — programme TV
specs:
  - specs/screens/tv-programme.md
modules:
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/stores/live.ts
  - live/api_views.py
tickets-tag: sprint-09
branche: claude/sprint/09-calendrier-tv
branche-parent: claude/sprint/08-calendrier-admin
log: backlog/sprints/09-calendrier-tv/log.md
---

# Sprint 09 — Calendrier : programme TV

**Objectif :** Greffer les surfaces publiques du calendrier sur la TV — slide
« Programme » dans le carousel TvIdle et bandeau « À suivre » sur TvScoreboard —
en branchant l'endpoint `/api/tv/upcoming/` livré au sprint 07.

## Définition de terminé

- Spec review sur `specs/screens/tv-programme.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-09` ouvert dans GitHub Issues (hors label `en-attente`)

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 09 — Calendrier : programme TV").

## Specs ciblées

- [`specs/screens/tv-programme.md`](../../../specs/screens/tv-programme.md)
  → fichiers : `TvIdle.vue`, `TvScoreboard.vue`, `TvLayout.vue`, `live/api_views.py`

---

## Tickets du sprint

> Tous les tickets sont dans GitHub Issues (milestone « Sprint 09 — Calendrier : programme TV »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#113](https://github.com/sirius911/moutilloux/issues/113) | live.ts : fetchUpcoming + upcoming[] [infra] | `stores/live.ts` | ⚠️ Fichier partagé — câblé par l'orchestrateur uniquement. Prérequis de #101 et #102 |
| [#101](https://github.com/sirius911/moutilloux/issues/101) | TvIdle : slide « Programme » (N prochains matchs planifiés) | `TvIdle.vue` | Dépend de #113 |
| [#102](https://github.com/sirius911/moutilloux/issues/102) | TvScoreboard : bandeau « À suivre » (next pendant un match en cours) | `TvScoreboard.vue` | Repositionner en bandeau bas + libellé "À suivre" |

---

## Périmètre backend

L'API TV est livrée (Sprint 07). Ce sprint est **100 % front-end**.
L'endpoint à consommer :

| Endpoint | Rôle |
|---|---|
| `GET /api/tv/upcoming/?n=5` | next + N prochains matchs planifiés + currentPlayDay |

---

## Ordre d'exécution suggéré

1. **#113 [infra — orchestrateur]** — Enrichir `live.ts` : ajouter `upcoming[]`,
   `currentPlayDay`, `fetchUpcoming()`. Fichier partagé, câblé par l'orchestrateur.
   Sans ce store, les tickets #101 et #102 ne peuvent pas lire `live.upcoming`.

2. **#101** — Ajouter la slide « Programme » dans `TvIdle.vue` : titre
   « Prochains matchs », liste des N matchs avec ~heure, "{A} vs {B}", étiquette de poule,
   marqueur « bientôt » sur le premier. Polling `fetchUpcoming` à ~4 s.

3. **#102** — Refactorer le PrepPanel de `TvScoreboard.vue` : déplacer en bandeau bas,
   reformuler en « À suivre — {A} vs {B} · Poule {X} » + mention d'appel des joueurs.

**Parallélisme :** #101 et #102 peuvent tourner en parallèle (fichiers disjoints)
une fois #113 câblé par l'orchestrateur.

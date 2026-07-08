---
sprint: 11
nom: Cycle de vie — statut & « Débuter »
specs:
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - competition/models.py
  - live/admin_views.py
  - live/bracket.py
  - live/api_views.py
  - live/urls.py
  - live/referee_views.py
  - frontend/app/src/stores/event.ts
  - frontend/app/src/types/index.ts
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminMatches.vue
tickets-tag: sprint-11
branche: claude/sprint/11-cycle-de-vie-statut
branche-parent: claude/sprint/10-contexte-url
log: backlog/sprints/11-cycle-de-vie-statut/log.md
---

# Sprint 11 — Cycle de vie : statut & « Débuter »

**Objectif :** Rendre l'avancement d'une épreuve **explicite** — un statut stocké
(`INSCRIPTION → EN_COURS → TERMINÉE`) et une transition **« Débuter »** qui génère
les matchs de poule, verrouille la composition, crée le squelette du tableau et
ouvre la planification. Fondation des sprints 12 et 13.

## Définition de terminé

- Champ `Event.status` en base (migration de schéma + de données OK)
- Endpoints `POST /api/events/<id>/{start,close,reopen}/` exposés et câblés
- **Golden path :** créer épreuve → composer poules → **Débuter** → matchs générés
  + poules verrouillées + squelette tableau posé + planification ouverte ;
  finale jouée → `TERMINÉE` (auto)
- Verrouillage des poules piloté par `status` (plus par « un match existe »)
- Spec review sur `specs/technical/cycle-de-vie-epreuve.md` (volet statut / Débuter)
  → verdict `✅ Conforme`
- Aucun ticket `sprint-11` ouvert dans GitHub Issues (hors `en-attente`)

## Specs ciblées

- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md)
  → §§ Machine à états, Transition « Débuter », Transition « Clôturer »
- Écrans impactés : [[admin-tournoi]], [[admin-poules]], [[admin-matchs]]

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 11 — Cycle de vie : statut & « Débuter » »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#121](https://github.com/sirius911/moutilloux/issues/121) | Modèle `Event.status` + migration | `competition/models.py` | ⚠️ Infra — orchestrateur. Prérequis de tout |
| [#122](https://github.com/sirius911/moutilloux/issues/122) | Services `start`/`close`/`reopen_event` | `admin_views.py`, `bracket.py`, `referee_views.py` | ⚠️ Infra — orchestrateur. Dépend de #121 |
| [#123](https://github.com/sirius911/moutilloux/issues/123) | Endpoints `/api/events/<id>/{start,close,reopen}/` | `api_views.py`, `urls.py` | ⚠️ Infra — orchestrateur. Dépend de #122 |
| [#124](https://github.com/sirius911/moutilloux/issues/124) | Verrouillage composition poules selon `status` | `admin_views.py` | Dépend de #121 |
| [#125](https://github.com/sirius911/moutilloux/issues/125) | Store : `status` typé + actions start/close/reopen | `stores/event.ts`, `types/index.ts` | ⚠️ Infra — orchestrateur. Dépend de #123 |
| [#126](https://github.com/sirius911/moutilloux/issues/126) | AdminTournoi : bouton « Débuter »/« Rouvrir » + modale | `AdminTournoi.vue` | Dépend de #125 |
| [#128](https://github.com/sirius911/moutilloux/issues/128) | AdminGroups : verrouillage par `status` + bandeau | `AdminGroups.vue` | Dépend de #125 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#127](https://github.com/sirius911/moutilloux/issues/127) | AdminTournoi : badge d'avancement dérivé de `status` | `AdminTournoi.vue` | Dépend de #125 |
| [#129](https://github.com/sirius911/moutilloux/issues/129) | AdminMatches : gating `EN_COURS` (retirer « Générer », état vide) | `AdminMatches.vue` | Dépend de #125 |

---

## Périmètre backend

Nouvelle **logique métier** (au-delà du « exposer/brancher ») : le champ `status`,
les services de transition (qui réutilisent `generate_group_matches_for_event` et
`ensure_final_bracket_exists`), et le verrouillage par statut. `live/urls.py` câblé
par l'orchestrateur uniquement.

## Ordre d'exécution suggéré

1. **#121 [infra]** — Modèle `Event.status` + migration. Prérequis absolu.
2. **#122 [infra]** — Services de transition (réutilise la génération existante).
3. **#123 [infra]** — Endpoints + `urls.py`.
4. **#124** — Verrouillage des services de composition par `status`. Peut être délégué.
5. **#125 [infra]** — Store + types.
6. **#126 / #127 / #128 / #129** — Front, **fichiers disjoints** → parallélisables.

**Parallélisme :** #124 (back) peut tourner pendant le front ; #126→#129 en parallèle
une fois #125 câblé par l'orchestrateur.

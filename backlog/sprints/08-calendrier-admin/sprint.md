---
sprint: 8
nom: Calendrier — écran admin
specs:
  - specs/screens/admin-matchs.md
  - specs/technical/planning.md
modules:
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/components/modals/GenerateMatchesModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
tickets-tag: sprint-08
branche: claude/sprint/08-calendrier-admin
branche-parent: claude/sprint/07-calendrier-api
log: backlog/sprints/08-calendrier-admin/log.md
---

# Sprint 08 — Calendrier : écran admin

**Objectif :** Remplacer le kanban `AdminMatches.vue` par la vue calendrier (journées + pile
à planifier + drag-and-drop + ETA + repos + pauses) décrite dans `specs/screens/admin-matchs.md`,
en branchant l'API calendrier livrée au sprint 07.

## Définition de terminé

- Spec review sur `specs/screens/admin-matchs.md` → verdict `✅ Conforme`
- Spec review sur `specs/technical/planning.md` → verdict `✅ Conforme` (côté front)
- Aucun ticket `sprint-08` ouvert dans GitHub Issues (hors label `en-attente`)

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 08 — Calendrier : écran admin").

## Specs ciblées

- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md)
  → fichiers : `AdminMatches.vue`, `EditMatchPanel.vue`, `GenerateMatchesModal.vue`,
    `stores/event.ts`, `live/api_views.py`, `live/admin_views.py`, `live/models.py`
- [`specs/technical/planning.md`](../../../specs/technical/planning.md)
  → fichiers : `live/models.py`, `live/api_views.py`, `live/admin_views.py`,
    `frontend/app/src/stores/event.ts`, `frontend/app/src/views/admin/AdminMatches.vue`

---

## Tickets du sprint

> Tous les tickets sont dans GitHub Issues (milestone « Sprint 08 — Calendrier : écran admin »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#94](https://github.com/sirius911/moutilloux/issues/94) | AdminMatches : refonte en calendrier (structure + packer + états + légende) | `AdminMatches.vue` | Ticket fondateur — à traiter en premier |
| [#95](https://github.com/sirius911/moutilloux/issues/95) | AdminMatches : drag-and-drop planifier / réordonner / dé-planifier | `AdminMatches.vue` | Dépend de #94 + #100 |
| [#96](https://github.com/sirius911/moutilloux/issues/96) | AdminMatches : moteur d'ETA + re-flow + alerte de capacité (front) | `AdminMatches.vue` | Dépend de #94 + #100 |
| [#97](https://github.com/sirius911/moutilloux/issues/97) | AdminMatches : détection du repos insuffisant (⚠) | `AdminMatches.vue` | Dépend de #94 |
| [#98](https://github.com/sirius911/moutilloux/issues/98) | AdminMatches : pré-poser + pauses (insérer / déplacer / retirer) | `AdminMatches.vue` | Dépend de #94 + #95 + #100 |
| [#99](https://github.com/sirius911/moutilloux/issues/99) | EditMatchPanel : onglet Planning revu (journée, heure estimée lecture seule, court retiré) | `EditMatchPanel.vue` | Dépend de #100 |
| [#100](https://github.com/sirius911/moutilloux/issues/100) | Store event.ts : état calendrier (fetchCalendar, CRUD playDays/breaks, autoArrange) **[infra]** | `stores/event.ts` | ⚠️ Fichier partagé — câblé par l'orchestrateur uniquement |

---

## Périmètre backend

L'API calendrier a été livrée au Sprint 07. Ce sprint est **100 % front-end**.
Les endpoints à consommer :

| Endpoint | Rôle dans cet écran |
|---|---|
| `GET /api/events/<id>/calendar/` | Packer calendrier : journées + pile + ETA |
| `POST /api/events/<id>/matches/reorder/` | Drag-and-drop (séquence complète) |
| `POST /api/events/<id>/matches/auto-arrange/` | Pré-pose |
| `GET/POST /api/events/<id>/playdays/` | Lister / créer journées |
| `PATCH/DELETE /api/playdays/<id>/` | Modifier / supprimer une journée |
| `POST /api/playdays/<id>/breaks/` | Ajouter une pause |
| `PATCH/DELETE /api/breaks/<id>/` | Modifier / supprimer une pause |
| `POST /api/matches/<id>/edit/` | Édition fine (statut, journée, mise en avant) |
| `POST /api/matches/<id>/feature/` | Mettre en avant |

---

## Ordre d'exécution suggéré

1. **#100 [infra — orchestrateur]** — Ajouter l'état calendrier dans `event.ts` : types
   `PlayDay`, `Break`, `CalendarData` ; actions `fetchCalendar`, `createPlayDay`,
   `updatePlayDay`, `deletePlayDay`, `createBreak`, `updateBreak`, `deleteBreak`,
   `autoArrange`. Sans ce store, les autres tickets ne peuvent pas se brancher sur l'API.

2. **#94** — Refonte complète de `AdminMatches.vue` : remplacer le kanban par la vue
   calendrier. Utilise `fetchCalendar` du store. Pas encore de drag-and-drop ni d'ETA.

3. **#99** — Révision de l'onglet Planning dans `EditMatchPanel.vue` : journée (sélecteur),
   heure estimée (lecture seule), court retiré, statut, mise en avant.

4. **#95** — Drag-and-drop sur `AdminMatches.vue` (vuedraggable) : planifier depuis la
   pile vers une journée, réordonner, dé-planifier. Appelle `reorder`.

5. **#96** — Moteur ETA + re-flow + alerte capacité, calculés côté front dans
   `AdminMatches.vue` à partir des données calendrier.

6. **#97** — Détection du repos insuffisant (⚠) côté front dans `AdminMatches.vue`.

7. **#98** — Bouton « Pré-poser » + gestion des pauses (insérer / déplacer / retirer).

**Parallélisme possible :** #94 et #99 peuvent tourner en parallèle (fichiers disjoints).
#95, #96, #97, #98 sont séquentiels (tous sur `AdminMatches.vue`).

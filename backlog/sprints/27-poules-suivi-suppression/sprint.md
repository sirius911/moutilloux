---
sprint: 27
nom: "Poules : suivi & suppression"
specs:
  - specs/screens/admin-poules.md
modules:
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/views/admin/AdminGroups.vue
tickets-tag: sprint-27
branche: claude/sprint/27-poules-suivi-suppression
branche-parent: main
log: backlog/sprints/27-poules-suivi-suppression/log.md
---

# Sprint 27 — Poules : suivi & suppression

**Objectif :** aligner `AdminGroups.vue` sur la spec Poules refondue
(décision 29) : l'écran a deux visages — composition en `INSCRIPTION`
(désormais avec suppression de poule), **suivi** en `EN_COURS` (classement
V/D/Pts + résultats des matchs par poule, badge Q légendé).

> Origine : revue produit 2026-07-07 (« on manque les infos des résultats des
> matchs dans l'admin », « les poules doivent pouvoir être supprimables »,
> « à quoi sert le Q ? »). Prérequis : sprint 26 (le badge Q affiché en mode
> suivi doit être le flag serveur corrigé).

## Définition de terminé

- Golden path : créer une poule vide → la supprimer (confirmation simple) ;
  poule avec 2 joueurs → suppression → les joueurs reviennent en « Non
  assignés » ; épreuve débutée → suppression refusée, l'écran bascule en mode
  suivi ; jouer un match via l'arbitre → score en direct puis résultat et
  classement recalculé visibles sans recharger.
- Spec review `✅ Conforme` sur [[admin-poules]].
- Aucune issue `sprint-27` ouverte.

## Specs ciblées

- [`specs/screens/admin-poules.md`](../../../specs/screens/admin-poules.md) — deux visages, suivi de poule, suppression, légende

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 27 — Poules : suivi & suppression »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#292](https://github.com/sirius911/moutilloux/issues/292) | Back : service + endpoint de suppression de poule (POST /api/groups/<id>/delete/) | `live/admin_views.py`, `live/api_views.py`, `live/urls.py` | `infra` — câblage urls.py par l'orchestrateur |
| [#293](https://github.com/sirius911/moutilloux/issues/293) | Front : AdminGroups — action « Supprimer la poule » (INSCRIPTION) | `frontend/app/src/views/admin/AdminGroups.vue` | dépend de #292 |
| [#294](https://github.com/sirius911/moutilloux/issues/294) | Back : api_event_groups — exposer les matchs de chaque poule (_pack_match) | `live/api_views.py` | |
| [#295](https://github.com/sirius911/moutilloux/issues/295) | Front : AdminGroups — mode suivi (classement V/D/Pts + résultats) dès EN_COURS | `frontend/app/src/views/admin/AdminGroups.vue` | dépend de #294 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#296](https://github.com/sirius911/moutilloux/issues/296) | Front : AdminGroups — légende du badge Q et des états | `frontend/app/src/views/admin/AdminGroups.vue` | avec #295 (même zone de template) |

---

## Périmètre backend

`delete_group` (service + endpoint) et enrichissement de `api_event_groups`
(matchs par poule). Aucune migration.

## Fichiers partagés (orchestrateur uniquement)

`live/urls.py` (route `groups/<id>/delete/`) — câblé par l'orchestrateur (#292).

## Ordre d'exécution suggéré

1. #292 ∥ #294 (back, fichiers distincts dans `api_views.py` mais attention aux
   conflits — séquentiel si même zone).
2. #293 puis #295 + #296 (front, même SFC → séquentiel).

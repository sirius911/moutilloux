---
sprint: 06
nom: Refacto Sélecteur & Joueurs
specs:
  - specs/screens/admin-shell.md
  - specs/screens/admin-joueurs.md
  - specs/screens/admin-inscriptions.md
  - specs/screens/admin-poules.md
  - specs/admin-panel-map.md
modules:
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/views/admin/AdminPlayers.vue
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - live/api_views.py
tickets-tag: sprint-06
branche: claude/sprint/06-refacto-selecteur
branche-parent: claude/sprint/05-admin-joueurs
log: backlog/sprints/06-refacto-selecteur/log.md
---

# Sprint 06 — Refacto Sélecteur & Joueurs

**Objectif :** Appliquer les décisions structurantes 15 et 16 — supprimer la licence joueur
de l'écran et de la modale, et déplacer le sélecteur d'épreuve de la sidebar vers le header
de chaque écran dépendant (Inscriptions, Poules).

## Définition de terminé

- Spec review sur toutes les specs listées → verdict `✅ Conforme`
- Aucun ticket `sprint-06` ouvert dans GitHub Issues (hors `en-attente`)

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 06 — Refacto Sélecteur & Joueurs").

## Specs ciblées

- [`specs/screens/admin-shell.md`](../../../specs/screens/admin-shell.md)
  → fichiers : `AdminLayout.vue`, `router/index.ts`, `stores/event.ts`, `stores/auth.ts`, `live/api_views.py`
- [`specs/screens/admin-joueurs.md`](../../../specs/screens/admin-joueurs.md)
  → fichiers : `AdminPlayers.vue`, `AddPlayerModal.vue`, `stores/event.ts`, `live/api_views.py`, `core/models.py`
- [`specs/screens/admin-inscriptions.md`](../../../specs/screens/admin-inscriptions.md)
  → fichiers : `AdminInscriptions.vue`, `CreateTeamModal.vue`, `stores/event.ts`, `live/api_views.py`, `live/admin_views.py`
- [`specs/screens/admin-poules.md`](../../../specs/screens/admin-poules.md)
  → fichiers : `AdminGroups.vue`, `AutoFillModal.vue`, `stores/event.ts`, `live/api_views.py`, `live/admin_views.py`
- [`specs/admin-panel-map.md`](../../../specs/admin-panel-map.md)
  → fichiers : `AdminLayout.vue`, `router/index.ts`

---

## Tickets du sprint

### 🟠 Majeures

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [#75](https://github.com/sirius911/moutilloux/issues/75) | AdminLayout : supprimer sélecteur d'épreuve de la sidebar (décision 16) | `AdminLayout.vue` |
| [#76](https://github.com/sirius911/moutilloux/issues/76) | AdminInscriptions : remplacer breadcrumb par sélecteur d'épreuve (décision 16) | `AdminInscriptions.vue` |
| [#77](https://github.com/sirius911/moutilloux/issues/77) | AdminGroups : remplacer breadcrumb par sélecteur d'épreuve (décision 16) | `AdminGroups.vue` |
| [#78](https://github.com/sirius911/moutilloux/issues/78) | AdminPlayers : retirer colonne Licence de la table (décision 15) | `AdminPlayers.vue` |
| [#79](https://github.com/sirius911/moutilloux/issues/79) | AdminPlayers : retirer filtre licenseNumber de la recherche (décision 15) | `AdminPlayers.vue` |
| [#80](https://github.com/sirius911/moutilloux/issues/80) | AddPlayerModal : retirer section Compétition et champ licence (décision 15) | `AddPlayerModal.vue` |
| [#81](https://github.com/sirius911/moutilloux/issues/81) | AdminGroups : bandeau de verrouillage absent (infra partagée — store requis) | `AdminGroups.vue`, `live/api_views.py` |
| [#82](https://github.com/sirius911/moutilloux/issues/82) | AdminInscriptions : window.confirm() → ConfirmModal pour retrait | `AdminInscriptions.vue` |

### 🟡 Mineures

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [#83](https://github.com/sirius911/moutilloux/issues/83) | AdminGroups : libellé "Auto-remplir" → "Remplir automatiquement" | `AdminGroups.vue` |
| [#84](https://github.com/sirius911/moutilloux/issues/84) | AdminGroups : message d'erreur dépôt générique → message serveur exact | `AdminGroups.vue` |
| [#85](https://github.com/sirius911/moutilloux/issues/85) | AdminInscriptions : supprimer les logs console | `AdminInscriptions.vue` |

---

## Périmètre backend

**`live/api_views.py`** — ticket #81 : ajouter un champ `locked: bool` dans la réponse de
`api_groups()`, dérivé de l'existence de matchs de poule pour l'épreuve.

**`stores/event.ts`** — ticket #81 : exposer `groupsLocked: boolean` (câblage par l'orchestrateur —
fichier partagé réservé).

---

## Ordre d'exécution suggéré

**Commencer par #75** (supprimer le sélecteur de la sidebar) : change `AdminLayout.vue` seul,
rapide, et évite d'avoir deux sélecteurs actifs pendant le sprint.

**Enchaîner #78 + #79 en parallèle** (licence dans la table et dans la recherche — même fichier
`AdminPlayers.vue`, sections disjointes). Puis **#80** (modale) indépendant.

**Puis #76 et #77 en parallèle** (ajout du sélecteur en header — fichiers disjoints).

**Puis #82** (ConfirmModal dans Inscriptions — indépendant).

**#81 en dernier** parmi les majeures : c'est le plus complexe (back + store partagé). L'agent
produit le plan et implémente la partie `api_views.py` + `AdminGroups.vue` ; l'orchestrateur
câble `event.ts`.

**Mineures #83, #84, #85** : toutes indépendantes, à traiter en dernière passe.

> **Note sprint 05 :** si les tickets #72 (champ naissance) et #73 (erreurs par champ modale)
> sont encore ouverts à l'entrée du sprint 06, la spec review de la session 1 les détectera
> et les re-milestonera si nécessaire.

---
sprint: 05
nom: Admin Joueurs
specs:
  - specs/admin-joueurs.md
modules:
  - live/api_views.py
  - frontend/app/src/types/index.ts
  - frontend/app/src/views/admin/AdminPlayers.vue
  - frontend/app/src/components/modals/AddPlayerModal.vue
tickets-tag: sprint-05
branche: claude/sprint/05-admin-joueurs
branche-parent: claude/sprint/04-admin-panel-map
log: backlog/sprints/05-admin-joueurs/log.md
---

# Sprint 05 — Admin Joueurs

**Objectif :** Combler les écarts entre l'écran `AdminPlayers.vue` / la modale
`AddPlayerModal.vue` et la spec `specs/admin-joueurs.md` — principalement exposer
`licenseNumber` dans l'API, l'afficher dans la table et dans la modale, et corriger
les petits écarts UX (genre optionnel, année seule, état vide différencié).

## Définition de terminé

- `api_players()` retourne `licenseNumber`
- Colonne Licence présente dans la table du registre
- Recherche filtre sur nom complet **et** numéro de licence
- Modale expose sections Contact (email + téléphone) et Compétition (licence)
- Spec review sur `specs/admin-joueurs.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-05` ouvert dans GitHub Issues

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 05 — Admin Joueurs").

## Tickets ouverts

### 🟠 Majeures (bloquantes)

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [#65](https://github.com/sirius911/moutilloux/issues/65) | API /api/players/ ne retourne pas licenseNumber | `live/api_views.py`, `frontend/app/src/types/index.ts` |
| [#66](https://github.com/sirius911/moutilloux/issues/66) | Colonne "Licence" absente de la table du registre | `AdminPlayers.vue` |
| [#67](https://github.com/sirius911/moutilloux/issues/67) | Recherche ne filtre pas sur le numéro de licence | `AdminPlayers.vue` |
| [#68](https://github.com/sirius911/moutilloux/issues/68) | Section Contact absente de la modale Fiche joueur | `AddPlayerModal.vue` |
| [#69](https://github.com/sirius911/moutilloux/issues/69) | Section Compétition absente de la modale Fiche joueur | `AddPlayerModal.vue` |

### 🟡 Mineures

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [#70](https://github.com/sirius911/moutilloux/issues/70) | État vide du registre non différencié de l'absence de résultats | `AdminPlayers.vue` |
| [#71](https://github.com/sirius911/moutilloux/issues/71) | Genre marqué requis dans la modale ; genderLabel('') retourne "Autre" | `AddPlayerModal.vue`, `AdminPlayers.vue` |
| [#72](https://github.com/sirius911/moutilloux/issues/72) | Champ "Année de naissance" = input type=date au lieu d'une année seule | `AddPlayerModal.vue` |
| [#73](https://github.com/sirius911/moutilloux/issues/73) | Erreurs de validation par champ non affichées dans la modale | `AddPlayerModal.vue` |

## Ordre d'exécution suggéré

**Commencer par #65** (API + types) : toutes les autres issues en dépendent.

Une fois `licenseNumber` exposé, traiter #66 et #67 en parallèle (même fichier
`AdminPlayers.vue`, mais sections disjointes — thead et computed).

Les issues #68 et #69 (modale) sont indépendantes du backend et peuvent tourner
en parallèle de #66/#67.

Les mineures (#70–#73) sont toutes indépendantes et peuvent être traitées en dernière passe.

---
sprint: 04
nom: Admin Panel Map
specs:
  - specs/admin-panel-map.md
modules:
  - frontend/app/src/router/index.ts
  - frontend/app/src/views/admin/AdminConfig.vue
  - frontend/app/src/views/admin/AdminLayout.vue
tickets-tag: sprint-04
branche: claude/sprint/04-admin-panel-map
branche-parent: claude/sprint/03-admin-shell
log: backlog/sprints/04-admin-panel-map/log.md
---

# Sprint 04 — Admin Panel Map

**Objectif :** Aligner la structure du panel admin sur les décisions structurantes de
`specs/admin-panel-map.md` — principalement supprimer l'écran Configuration du routeur
et de l'arborescence front, et reprendre les gaps shell non encore fermés.

## Définition de terminé

- Route `/admin/config` absente du routeur, `AdminConfig.vue` supprimé
- Spec review sur `specs/admin-panel-map.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-04` ouvert dans GitHub Issues

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 04 — Admin Panel Map").

## Specs ciblées

- [`specs/admin-panel-map.md`](../../../specs/admin-panel-map.md)
  → fichiers : `AdminLayout.vue`, `router/index.ts`, `admin.jsx`, `extras.jsx`,
  `live/api_views.py`, `live/admin_views.py`

---

## Périmètre backend

Aucun endpoint à modifier. Toutes les mutations listées dans la spec
(`/api/editions/`, bracket assign/clear, CRUD épreuves, etc.) sont câblées dans
`live/urls.py`. La cohérence API est ✅ conforme.

---

## Ordre d'exécution suggéré

Les tickets 050 et 060 touchent tous les deux `router/index.ts` → les traiter en une
seule passe pour éviter deux touches sur le même fichier partagé. Le ticket 060 doit
s'exécuter après que sprint-03 ait fermé le 055 (même décision 11).

Le ticket 040 est indépendant (fichiers `AdminGroups.vue` + `AdminMatches.vue`), il peut
tourner en parallèle. C'est le plus complexe des trois : déplacer le bouton + la modale
`GenerateMatchesModal` vers `AdminMatches.vue` et s'assurer que le kanban se rafraîchit
après génération.

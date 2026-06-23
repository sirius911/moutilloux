---
sprint: 03
nom: Admin Shell
specs:
  - specs/screens/admin-shell.md
modules:
  - frontend/app/src/views/admin/AdminLayout.vue
tickets-tag: sprint-03
branche: claude/sprint/03-admin-shell
branche-parent: sprint/02-admin-tournoi
log: backlog/sprints/03-admin-shell/log.md
---

# Sprint 03 — Admin Shell

**Objectif :** Aligner `AdminLayout.vue` sur la spec `admin-shell.md` — navigation
à 6 entrées avec compteurs, sélecteur épreuve robuste, sous-titre de marque dynamique,
gestion d'erreur au montage.

## Définition de terminé

- Spec review sur `specs/screens/admin-shell.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-03` ouvert dans GitHub Issues

> Les tickets sont gérés dans GitHub Issues (milestone "Sprint 03 — Admin Shell").

## Specs ciblées

- [`specs/screens/admin-shell.md`](../../../specs/screens/admin-shell.md)
  → fichiers : `AdminLayout.vue`, `router/index.ts`, `stores/event.ts`, `stores/auth.ts`,
  `live/api_views.py`

---

## Périmètre backend

Aucun endpoint à créer ou modifier : toutes les corrections sont front-only.
`fetchAllPlayers()` pour le compteur Joueurs (ticket 056) appelle un endpoint existant
(`GET /api/players/`) déjà câblé dans `event.ts`.

---

## Ordre d'exécution suggéré

```
058 (sous-titre)        → 1 ligne, rapide, sans dépendance
059 (try/catch montage) → trivial, sans dépendance
055 (supprimer Config)  → trivial, sans dépendance
057 (sélecteur vide)    → front seul, sans dépendance
056 (compteurs)         → le plus complexe : transformer navItems en computed,
                          ajouter fetchAllPlayers() au montage, badge template
```

Les tickets 055, 057, 058, 059 sont indépendants et peuvent être traités en parallèle.
Le ticket 056 est le plus lourd et doit être traité en dernier ou en parallèle
avec les autres par un agent dédié.

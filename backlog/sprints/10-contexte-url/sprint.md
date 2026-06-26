---
sprint: 10
nom: Contexte d'épreuve (URL)
specs:
  - specs/technical/routing-context.md
modules:
  - frontend/app/src/router/index.ts
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminBracket.vue
tickets-tag: sprint-10
branche: claude/sprint/10-contexte-url
branche-parent: claude/sprint/09-calendrier-tv
log: backlog/sprints/10-contexte-url/log.md
---

# Sprint 10 — Contexte d'épreuve (URL)

**Objectif :** Porter l'épreuve active dans l'URL admin (`/admin/events/:eventId/…`)
pour qu'elle survive au rechargement et aux partages de lien, conformément à la spec
`routing-context.md`.

## Définition de terminé

- Spec review sur `specs/technical/routing-context.md` → verdict `✅ Conforme`
- Aucun ticket `sprint-10` ouvert dans GitHub Issues (hors label `en-attente`)
- Rechargement sur `/admin/events/42/groups` → mêmes données qu'avant rechargement
- Lien périmé `/admin/events/999/groups` → redirigé silencieusement vers épreuve par défaut

## Specs ciblées

- [`specs/technical/routing-context.md`](../../../specs/technical/routing-context.md)
  → fichiers : `router/index.ts`, `stores/event.ts`, `AdminLayout.vue`,
  `AdminInscriptions.vue`, `AdminGroups.vue`, `AdminMatches.vue`, `AdminBracket.vue`

---

## Tickets du sprint

> Tous les tickets sont dans GitHub Issues (milestone « Sprint 10 — Contexte d'épreuve (URL) »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#115](https://github.com/sirius911/moutilloux/issues/115) | Router : routes admin vers `/admin/events/:eventId/…` | `router/index.ts` | ⚠️ Infra partagée — orchestrateur uniquement. Prérequis de tous les autres |
| [#116](https://github.com/sirius911/moutilloux/issues/116) | AdminLayout : sidebar avec `:eventId` + watcher de route | `AdminLayout.vue` | ⚠️ Infra partagée — orchestrateur uniquement. Dépend de #115 |
| [#117](https://github.com/sirius911/moutilloux/issues/117) | Sélecteur d'épreuve : `router.push` (3 écrans) | `AdminInscriptions.vue`, `AdminGroups.vue`, `AdminMatches.vue` | Dépend de #115 + #116 |
| [#118](https://github.com/sirius911/moutilloux/issues/118) | Garde de route : résolution/validation `:eventId` | `router/index.ts` | ⚠️ Infra partagée — orchestrateur uniquement. Dépend de #115 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#119](https://github.com/sirius911/moutilloux/issues/119) | Écrans dépendants : état vide « Aucune épreuve active » | 4 écrans | Dépend de #115 + #118 |

---

## Périmètre backend

**Aucun.** Ce sprint est 100 % front-end. Aucun nouvel endpoint API n'est requis.
La résolution repose sur l'existant `GET /api/editions/`.

---

## Ordre d'exécution suggéré

1. **#115 [infra — orchestrateur]** — Réécrire les routes admin avec `:eventId`.
   Prérequis absolu : sans cette route, aucune URL portant l'épreuve n'existe.

2. **#118 [infra — orchestrateur]** — Ajouter la garde de route (`beforeEnter`)
   sur la route parent `/admin/events/:eventId`. À enchaîner avec #115 (même fichier).

3. **#116 [infra — orchestrateur]** — Mettre à jour `AdminLayout.vue` :
   watcher de route + liens de sidebar dynamiques. À câbler après les routes.

4. **#117** — Les 3 écrans à `setActiveEvent` → `router.push`. Peut être délégué à
   un agent car les 3 fichiers sont disjoints et le pattern est identique.

5. **#119** — État vide sur 4 écrans. Peut être délégué à un agent (pattern identique,
   fichiers disjoints). Dernier car dépend que la garde (#118) laisse passer sans épreuve.

**Parallélisme :** #117 et #119 peuvent tourner en parallèle une fois #115 + #116 + #118
câblés par l'orchestrateur.

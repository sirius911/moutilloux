---
sprint: 37
nom: "Mobile : arbitre & régie"
specs:
  - specs/transverse/mobile.md
  - specs/screens/admin-regie-mobile.md
  - specs/screens/arbitre-match.md
modules:
  - frontend/app/src/router/index.ts
  - frontend/app/src/composables/
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/index.html
  - frontend/app/public/
tickets-tag: sprint-37
branche: claude/sprint/37-mobile-arbitre-regie
branche-parent: main
log: backlog/sprints/37-mobile-arbitre-regie/log.md
---

# Sprint 37 — Mobile : arbitre & régie

**Objectif :** les surfaces téléphone de l'application — scène mobile portrait
de la saisie arbitre (zones haut/bas, verrou anti-tap) et de l'accueil arbitre,
écran **régie admin** `/admin/regie` (gestes chauds : fil de journée, actions
match, annonces), PWA minimale et wake-lock. Le reste de l'admin demeure
desktop, assumé.

> Origine : retours produit 2026-07-08 (problématique 6). Specs neuves :
> [[mobile]] (socle) et [[admin-regie-mobile]] (écran). Philosophie « scène
> fixe scalée » conservée (seconde scène ~390×844 via `useScale`). **Aucun
> endpoint back neuf** — la régie réutilise calendrier, actions match et CRUD
> annonces existants. Dernier sprint de la série : il bénéficie de
> l'échauffement (36) et du bracket au calendrier (34) déjà en place.

## Définition de terminé

- Golden path arbitre : sur un viewport 390 px — accueil en liste verticale,
  ouvrir le match, démarrer (échauffement), lancer, **scorer point par point
  en zones haut/bas**, verrouiller/déverrouiller les zones, terminer ; sur
  iPad, rien n'a changé (scène 834×1112).
- Golden path régie : sur téléphone — `/admin/regie` (refusé non-admin) montre
  le fil du jour avec ponctualité et match en cours épinglé ; démarrer le
  next, corriger un score, publier une annonce qui apparaît sur la TV.
- PWA : « Ajouter à l'écran d'accueil » → l'app s'ouvre en plein écran avec
  son icône ; l'écran de saisie ne se met pas en veille pendant un match LIVE.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[mobile]] et [[admin-regie-mobile]].
- Aucune issue `sprint-37` ouverte.

## Specs ciblées

- [`specs/transverse/mobile.md`](../../../specs/transverse/mobile.md) — socle (scènes, PWA, wake-lock, verrou)
- [`specs/screens/admin-regie-mobile.md`](../../../specs/screens/admin-regie-mobile.md) — écran régie
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — § Variante mobile

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 37 — Mobile : arbitre & régie »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#337](https://github.com/sirius911/moutilloux/issues/337) | Infra : sélection de scène mobile (viewport) + route /admin/regie | `router/index.ts`, `composables/` | `infra` — orchestrateur, débloque tout |
| [#338](https://github.com/sirius911/moutilloux/issues/338) | Front : ArbitreMatch — scène mobile portrait + verrou anti-tap | `ArbitreMatch.vue` | dépend de #337 |
| [#339](https://github.com/sirius911/moutilloux/issues/339) | Front : ArbitreHome — variante mobile | `ArbitreHome.vue` | dépend de #337 |
| [#340](https://github.com/sirius911/moutilloux/issues/340) | Front : AdminRegie — fil de journée + actions + annonces | `AdminRegie.vue` (neuve) | dépend de #337 (route) |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#341](https://github.com/sirius911/moutilloux/issues/341) | Front : PWA minimale (manifest + icônes + standalone) | `index.html`, `public/` | indépendant |
| [#342](https://github.com/sirius911/moutilloux/issues/342) | Front : wake-lock saisie arbitre (useWakeLock) | `composables/`, `ArbitreMatch.vue` | `infra` — composable par l'orchestrateur ; branchement dans #338 |

---

## Périmètre backend

Aucun.

## Fichiers partagés (orchestrateur uniquement)

- `router/index.ts` + nouveaux composables (`useViewport`, `useWakeLock`) —
  #337 et #342 sont des tickets **orchestrateur** ; les agents `vue-screen` ne
  touchent que leur SFC.

## Ordre d'exécution suggéré

1. #337 (orchestrateur : viewport + route) et le composable de #342 — en tête.
2. #338 ∥ #339 ∥ #340 (trois SFC disjointes, trois `vue-screen` en parallèle).
3. #341 (indépendant, à tout moment).

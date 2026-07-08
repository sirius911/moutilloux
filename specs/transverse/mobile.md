---
type: transverse
module: mobile
fichiers:
  - frontend/app/src/composables/useScale.ts
  - frontend/app/src/router/index.ts
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/index.html
  - frontend/app/vite.config.ts
---

# Spec transverse — Mobile (arbitre + régie admin)

> Le socle commun des surfaces **téléphone** de l'application : quelles
> surfaces existent en mobile, comment une scène mobile est sélectionnée et
> rendue, et les comportements transverses (PWA, wake-lock, verrou anti-tap).
> Issu des retours du 2026-07-08. Les écrans eux-mêmes sont décrits dans
> [[arbitre-match]] (variante mobile) et [[admin-regie-mobile]].

## Principe : des gestes, pas des écrans

On ne « porte » pas l'application sur mobile : on identifie les gestes qui se
font **debout, au bord du court**, et on leur donne une surface téléphone.
Tout le reste demeure sur ses cibles existantes (desktop admin, iPad arbitre,
TV 1080p).

| Surface | Mobile | Description |
|---|---|---|
| **Arbitre — saisie** (`/arbitre/:matchId`) | ✓ variante mobile | scoring point par point au téléphone ([[arbitre-match]]) |
| **Arbitre — accueil** (`/arbitre`) | ✓ variante mobile | programme du jour + accès au match (liste verticale, déjà proche d'un layout mobile) |
| **Admin — régie** (`/admin/regie`) | ✓ écran dédié | les gestes chauds de l'organisateur ([[admin-regie-mobile]]) |
| Admin complet (poules, seeding, drag du calendrier, affiches) | ✗ | reste desktop — le drag-and-drop n'a pas de bonne traduction tactile étroite |
| TV | ✗ | cible 1080p uniquement |

## Sélection de scène

- Les écrans arbitre restent sur leurs **routes existantes** : la variante est
  choisie **par viewport** (largeur < ~600 px → scène mobile), pas par route.
  Un iPad garde la scène 834×1112 actuelle.
- La scène mobile est une **seconde scène fixe portrait ~390 × 844**, mise à
  l'échelle par le même `useScale` (letterboxing léger selon les téléphones).
  On reste dans la philosophie « scène fixe scalée » du projet — pas de
  responsive fluide.
- La régie admin est une **route dédiée** (`/admin/regie`, garde `isAdmin`) —
  pas une adaptation des écrans admin existants.

## PWA minimale

- **Manifest** (nom, icônes, `display: standalone`, orientation portrait) pour
  l'installation sur l'écran d'accueil et le plein écran.
- **Pas de service worker hors-ligne** : le mode en ligne reste la règle
  (v1, [[arbitre-match]]) — un tap perdu est perdu, le polling resynchronise.
  Le rejeu hors-ligne reste hors périmètre.

## Wake-lock

- Sur l'écran de **saisie arbitre** (toutes tailles, iPad compris), l'écran ne
  doit pas se verrouiller pendant un match `LIVE` : **Screen Wake Lock API**,
  demandé au montage quand le match est `LIVE`, relâché sinon (et re-demandé
  au retour de visibilité — l'API le perd quand l'onglet est caché).
- Échec de l'API (navigateur non compatible) : silencieux, aucun message.

## Verrou anti-tap (saisie arbitre mobile)

- Un bouton **cadenas** gèle les zones de tap (état local à l'écran) : le
  téléphone vit dans une main ou une poche, un tap accidentel est un point.
- Déverrouillage volontaire (appui long ou double-tap sur le cadenas — à
  trancher au design). Le verrou ne bloque que les zones de score, pas la
  consultation.

## Hors périmètre

- Mode hors-ligne / rejeu de taps (inchangé, v1 en ligne).
- Admin complet responsive.
- Notifications push.

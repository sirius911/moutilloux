---
sprint: 41
nom: "Joueurs : photo caméra"
specs:
  - specs/screens/admin-joueurs.md
modules:
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/components/modals/CameraCaptureModal.vue
tickets-tag: sprint-41
branche: claude/sprint/41-joueurs-photo-camera
branche-parent: main
log: backlog/sprints/41-joueurs-photo-camera/log.md
---

# Sprint 41 — Joueurs : photo caméra

**Objectif :** un bouton « Prendre une photo » sur le champ Photo de la fiche
joueur — appli photo native sur téléphone/tablette (attribut `capture`,
compatible avec l'accès HTTP par IP locale), modale webcam in-app
(`getUserMedia`) sur desktop. La photo capturée rejoint le circuit d'upload
existant, aucun endpoint nouveau.

> Origine : retours produit 2026-07-09 (problématique 3 — « pouvoir prendre
> une photo avec son appareil, que ce soit le Mac ou le téléphone »).
> Arbitrage : chemin natif sur mobile (getUserMedia y serait bloqué en HTTP),
> webcam in-app sur desktop (localhost = origine sécurisée). La photo reste la
> matière première des affiches de match ([[affiche-match]]).

## Définition de terminé

- Golden path desktop : « Prendre une photo » → aperçu webcam → cliché →
  « Reprendre » ou « Utiliser » → aperçu dans la fiche → enregistrement →
  avatar mis à jour dans le registre ; refuser la permission caméra → message
  explicite, le téléversement reste utilisable ; la LED caméra s'éteint à la
  fermeture de la modale.
- Golden path mobile : sur téléphone (HTTP, IP locale), « Prendre une photo »
  ouvre l'appli photo native, la prise revient en aperçu et s'uploade.
- Contraintes existantes respectées (format, ≤ 10 Mo) ; suppression et
  remplacement de photo inchangés.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[admin-joueurs]].
- Aucune issue `sprint-41` ouverte.

## Specs ciblées

- [`specs/screens/admin-joueurs.md`](../../../specs/screens/admin-joueurs.md) — §Prendre une photo (modale Fiche joueur)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 41 — Joueurs : photo caméra »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#357](https://github.com/sirius911/moutilloux/issues/357) | Front : fiche joueur — « Prendre une photo » sur téléphone (appli photo native) | `AddPlayerModal.vue` | pose le bouton + le routage par appareil |
| [#358](https://github.com/sirius911/moutilloux/issues/358) | Front : fiche joueur — modale webcam desktop (getUserMedia) | `CameraCaptureModal.vue` (neuve), `AddPlayerModal.vue` | après #357 (branchement dans le même champ) |

### 🟡 Mineures

Aucune.

---

## Périmètre backend

Aucun — `POST /api/players/<id>/photo/` (multipart) est réutilisé tel quel.

## Fichiers partagés (orchestrateur uniquement)

Aucun (la détection d'appareil réutilise l'existant du sprint 37 si adaptée ;
si un composable partagé devait être touché, l'orchestrateur reprend la main).

## Ordre d'exécution suggéré

1. #357 — bouton, input `capture`, routage par appareil (l'essentiel du champ).
2. #358 — la modale webcam vient se brancher sur le bouton posé par #357
   (même zone d'`AddPlayerModal.vue` → séquentiel, même agent de préférence).

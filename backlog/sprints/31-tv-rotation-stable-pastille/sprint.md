---
sprint: 31
nom: "TV : rotation stable & pastille de progression"
specs:
  - specs/screens/tv-live.md
modules:
  - frontend/app/src/views/tv/TvIdle.vue
tickets-tag: sprint-31
branche: claude/sprint/31-tv-rotation-stable-pastille
branche-parent: main
log: backlog/sprints/31-tv-rotation-stable-pastille/log.md
---

# Sprint 31 — TV : rotation stable & pastille de progression

**Objectif :** décision 12 de [[tv-map]] — la rotation du carousel idle
devient **stable** (un rafraîchissement des données ne change jamais la slide
affichée ; les changements de composition prennent effet au tick suivant) et
la pastille de pagination de la slide courante se **remplit** sur ses ~8 s.

> Origine : revue produit 2026-07-07 — slides inconsistantes observées
> (diagnostic : `SLIDES` recalculé à chaque poll de 10 s + index positionnel).
> La cadence reste 8 s (confirmée). Sprint 100 % front, une seule SFC.

## Définition de terminé

- Golden path : pendant la slide Poules, activer/désactiver une annonce depuis
  l'admin → la slide Poules reste affichée jusqu'au bout de ses 8 s ; la slide
  Annonces (dés)apparaît au cycle suivant ; le pager ne saute pas.
- La pastille active se remplit visiblement sur la durée de la slide et repart
  de zéro à chaque changement (rotation et `goTo`).
- Spec review `✅ Conforme` sur [[tv-live]] (§ Cadre du carousel).
- Aucune issue `sprint-31` ouverte.

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — rotation stable, pastille de progression

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 31 — TV : rotation stable & pastille de progression »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#308](https://github.com/sirius911/moutilloux/issues/308) | Front : TvIdle — rotation stable (un refresh ne change jamais la slide affichée) | `frontend/app/src/views/tv/TvIdle.vue` | **avant** #309 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#309](https://github.com/sirius911/moutilloux/issues/309) | Front : TvIdle — pastille de pagination qui se remplit | `frontend/app/src/views/tv/TvIdle.vue` | dépend de #308 (le reset s'accroche au changement de slide) |

---

## Périmètre backend

Aucun.

## Fichiers partagés (orchestrateur uniquement)

Aucun.

## Ordre d'exécution suggéré

#308 puis #309 (même SFC, la pastille s'accroche à la mécanique de rotation
stabilisée).

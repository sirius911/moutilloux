---
sprint: 39
nom: "TV : échauffement, score au tableau & carrousel"
specs:
  - specs/screens/tv-live.md
  - specs/screens/admin-tableau-final.md
modules:
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/admin/AdminBracket.vue
tickets-tag: sprint-39
branche: claude/sprint/39-tv-echauffement-score-carrousel
branche-parent: main
log: backlog/sprints/39-tv-echauffement-score-carrousel/log.md
---

# Sprint 39 — TV : échauffement, score au tableau & carrousel

**Objectif :** trois retouches d'affichage arbitrées le 2026-07-09 — corriger
la scène échauffement sans affiche (bloc central unique, suppression du calque
typo qui se superposait au chrono), afficher le **score par sets** dans la
slide Tableau du carrousel **et** dans le bracket admin, et élargir légèrement
l'emprise des slides du carrousel.

> Origine : retours produit 2026-07-09 (problématiques 2-bis, 5 et 6). Travail
> **100 % front** : les scores sont déjà dans les payloads (`setScores`,
> `setsA/B`, `gamesA/B` de `_pack_match`, servis par `_pack_event_bracket`
> aux deux écrans). S'appuie sur les sprints 36 (échauffement) et 22 (carousel)
> sans rien y redupliquer.

## Définition de terminé

- Golden path échauffement : démarrer un match **sans affiche** avec deux noms
  longs → scène lisible (fond de court + bloc central ÉCHAUFFEMENT/chrono/
  joueurs/étape/court), aucune superposition ; la variante **avec affiche**
  est inchangée.
- Golden path score : un quart **terminé** affiche son score par sets dans la
  slide Tableau TV **et** dans AdminBracket ; une demie **en cours** montre
  sets acquis + jeux du set courant, qui évoluent au poll sans recharger.
- Les slides du carrousel exploitent ~1760 px utiles (poules, tableau + 3e
  place et programme vérifiés à 1920×1080), en-tête et pied inchangés.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[tv-live]] et [[admin-tableau-final]].
- Aucune issue `sprint-39` ouverte.

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — état ÉCHAUFFEMENT, slide Tableau, emprise des slides
- [`specs/screens/admin-tableau-final.md`](../../../specs/screens/admin-tableau-final.md) — score par sets sur les places du bracket

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 39 — TV : échauffement, score au tableau & carrousel »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#351](https://github.com/sirius911/moutilloux/issues/351) | Front : TvScoreboard — échauffement sans affiche : bloc central unique | `TvScoreboard.vue` | indépendant |
| [#352](https://github.com/sirius911/moutilloux/issues/352) | Front : TvIdle — slide Tableau : score par sets sur chaque ligne joueur | `TvIdle.vue` | même fichier que #354 |
| [#353](https://github.com/sirius911/moutilloux/issues/353) | Front : AdminBracket — score par sets sur les places du bracket | `AdminBracket.vue` | même présentation que #352 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#354](https://github.com/sirius911/moutilloux/issues/354) | Front : TvIdle — élargir l'emprise des slides (~1760 px) | `TvIdle.vue` | après #352 (même fichier) |

---

## Périmètre backend

Aucun.

## Fichiers partagés (orchestrateur uniquement)

Aucun — trois SFC d'écran, pas de store ni de composable touché.

## Ordre d'exécution suggéré

1. #351 ∥ (#352 → #354) ∥ #353 — trois chantiers parallèles (SFC disjointes) ;
   #352 et #354 partagent `TvIdle.vue` → même agent, en séquence.
2. #352 et #353 partagent la présentation « chiffres par set alignés à
   droite » : converger sur le même rendu (l'orchestrateur arbitre si besoin).

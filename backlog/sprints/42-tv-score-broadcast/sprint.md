---
sprint: 42
nom: "TV : score broadcast et phase en grand"
specs:
  - specs/screens/tv-live.md
  - specs/technical/tv-state.md
modules:
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/types/index.ts
  - live/api_views.py
tickets-tag: sprint-42
branche: claude/sprint/42-tv-score-broadcast
branche-parent: main
log: backlog/sprints/42-tv-score-broadcast/log.md
---

# Sprint 42 — TV : score broadcast et phase en grand

**Objectif :** aligner le scoreboard TV sur les retours du 2026-07-10 — la
bande de score passe en deux lignes façon broadcast (nom, sets, jeux du set en
cours en dominant et points sur la ligne de chaque joueur), et le mini-tableau
d'enjeu est remplacé par la phase en grand (« Quart de finale »,
« Demi-finale », « Finale », « 3e place ») pour les matchs de tableau.

> Origine : retours produit 2026-07-10 (2 problématiques : le panneau tableau
> masque un nom et n'apporte rien ; on ne peut pas attribuer les jeux géants à
> un joueur). Specs mises à jour le même jour : décision 13 de [[tv-map]],
> §« Bande basse » et §« L'enjeu du match » de [[tv-live]], contrat `stake`
> réduit dans [[tv-state]]. Le panneau de classement de poule et la carte
> « À préparer » (sprints 35/39) sont conservés tels quels.

## Définition de terminé

- Golden path **poule** : match de poule LIVE → bande basse deux lignes, les
  jeux du set en cours sur la ligne de chaque joueur (colonnes SETS /
  JEUX · SET {n} / POINTS étiquetées), panneau de classement entier au-dessus
  de la bande, aucun chevauchement.
- Golden path **tableau** : match de quart LIVE → « Quart de finale » en grand
  au-dessus du score, aucun panneau à gauche, les deux noms entièrement
  visibles ; `GET /api/tv/state/` renvoie `"stake": null`.
- Aucun accent décoratif (le chiffre du côté A n'est plus jaune) ; le signal
  « AV » en accent et la balle de service sont conservés.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur [[tv-live]] et [[tv-state]].
- Aucune issue `sprint-42` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) —
  §« Bande basse : le score broadcast », §« L'enjeu du match », états limites.
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) —
  contrat `stake` (variante bracket retirée).

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 42 — TV : score broadcast et
> phase en grand »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#361](https://github.com/sirius911/moutilloux/issues/361) | Front : TV — bande de score broadcast (deux lignes, une par joueur) | `TvScoreboard.vue` | inclut le retrait de l'accent décoratif côté A |
| [#362](https://github.com/sirius911/moutilloux/issues/362) | Front : TV — match de tableau : phase en grand, mini-tableau retiré | `TvScoreboard.vue` | après #361 (même fichier) |
| [#363](https://github.com/sirius911/moutilloux/issues/363) | Back : tv/state — retirer la variante bracket du stake | `live/api_views.py` | indépendant (contrat déjà nul côté affichage après #362) |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#364](https://github.com/sirius911/moutilloux/issues/364) | Front : types — retirer la variante bracket de TvStake | `types/index.ts` | `infra` — orchestrateur, avec/après #362 (narrowing vue-tsc) |
| [#365](https://github.com/sirius911/moutilloux/issues/365) | Front : TV — le panneau d'enjeu ne recouvre jamais la bande de score | `TvScoreboard.vue` | après #361 (position de la bande connue) |

> #362, #363 et #364 partagent la même cause racine (retrait du mini-tableau,
> décision 13) : ils se closent naturellement ensemble.

---

## Périmètre backend

`live/api_views.py` uniquement : suppression de la branche bracket de
`_pack_tv_stake` (#363). Pas de route nouvelle, pas de service extrait —
`_pack_event_bracket` reste utilisé par `GET /api/events/<id>/bracket/` et
`tv/idle`.

## Fichiers partagés (orchestrateur uniquement)

`frontend/app/src/types/index.ts` (#364, label `infra`) : type `TvStake`
consommé par le store `live` — l'orchestrateur l'édite après le retrait du
bloc bracket dans la SFC. `stores/live.ts` n'a pas besoin de changer (le ref
`stake` est déjà typé `TvStake | null`).

## Ordre d'exécution suggéré

1. **#361** (front, bande broadcast) ∥ **#363** (back, stake) — fichiers
   disjoints, parallélisables.
2. **#362** — même fichier que #361 → séquentiel, même agent de préférence.
3. **#365** — cale le panneau de poule sur la bande posée par #361 (même
   fichier → séquentiel).
4. **#364** — orchestrateur, une fois #362 mergé (`vue-tsc` doit passer).

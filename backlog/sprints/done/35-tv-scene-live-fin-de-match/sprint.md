---
sprint: 35
nom: "TV : scène live & fin de match"
specs:
  - specs/screens/tv-live.md
  - specs/technical/tv-state.md
modules:
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/stores/live.ts
tickets-tag: sprint-35
branche: claude/sprint/35-tv-scene-live-fin-de-match
branche-parent: main
log: backlog/sprints/35-tv-scene-live-fin-de-match/log.md
---

# Sprint 35 — TV : scène live & fin de match

**Objectif :** recomposer la scène live de la TV pour que le **score soit
l'élément dominant** — centre « editorial » (jeux géants + label), carte
« À préparer » flottante haut-droite (retour au PrepPanel du design), panneau
d'enjeu latéralisé — et ajouter l'écran **vainqueur ~30 s** en fin de match
(fenêtre côté front, photo finish).

> Origine : retours produit 2026-07-08 (problématiques 2 et 3). Références
> design : `frontend/design/scoreboard.jsx` (`ScoreboardEditorial` :233,
> `PrepPanel` :50) et `scoreboard.css` (`.tv-prep`) — c'est majoritairement du
> **portage**, pas de la création. S'appuie sur le sprint 33 (points
> `displayPointA/B` + AV accent) sans le redupliquer. Aucun changement back.

## Définition de terminé

- Golden path scène : match LIVE → jeux du set en très grand au centre avec
  « JEUX · SET {n} », lignes joueurs (service, nom, points, sets), affiche en
  fond ; carte « À préparer » en haut à droite si un next existe (absente
  sinon) ; enjeu à gauche en ~480 px (classement de poule ou mini-tableau
  condensé), masqué si `stake` nul ; tie-break → points bruts + badge.
- Golden path fin de match : balle de match → scène « photo finish » (~30 s :
  affiche plein écran, VICTOIRE + nom, score par sets, durée) puis fondu vers
  le carousel ; démarrer un autre match pendant la fenêtre → le direct
  préempte ; abandon → mention « Abandon » ; walkover → aucune scène.
- `npx vue-tsc --noEmit` passe ; rendu vérifié sur cible TV 1080p.
- Spec review `✅ Conforme` sur [[tv-live]] (états SCOREBOARD et FIN DE MATCH)
  et [[tv-state]] (§ Front).
- Aucune issue `sprint-35` ouverte.

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — scène composée + état FIN DE MATCH
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) — fenêtre fin de match côté store (fetch one-shot)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 35 — TV : scène live & fin de match »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#329](https://github.com/sirius911/moutilloux/issues/329) | Front : centre « editorial » (jeux géants + label, lignes joueurs) | `TvScoreboard.vue` | structure de la scène — en premier |
| [#330](https://github.com/sirius911/moutilloux/issues/330) | Front : carte « À préparer » (PrepPanel) haut-droite | `TvScoreboard.vue` | après #329 (même fichier) |
| [#331](https://github.com/sirius911/moutilloux/issues/331) | Front : panneau d'enjeu latéralisé (~480 px, gauche) | `TvScoreboard.vue` | après #329 (même fichier) |
| [#332](https://github.com/sirius911/moutilloux/issues/332) | Front : scène « Fin de match » ~30 s (store + photo finish) | `live.ts`, `TvScoreboard.vue` | `infra` — store partagé, orchestrateur |

---

## Périmètre backend

Aucun (le contrat `tv/state` est inchangé ; le fetch one-shot réutilise
`GET /api/matches/:id/` existant).

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/stores/live.ts` (#332 : fenêtre `finishedHero`) —
  l'orchestrateur écrit le store ; l'agent d'écran ne touche que la SFC.

## Ordre d'exécution suggéré

Tout vit dans `TvScoreboard.vue` → **séquentiel** : #329 (nouvelle structure de
scène) → #330 → #331 → #332 (la scène photo finish s'ajoute en dernier, le
store étant câblé par l'orchestrateur en parallèle de #330/#331).

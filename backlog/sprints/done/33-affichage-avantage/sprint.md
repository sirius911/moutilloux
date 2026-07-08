---
sprint: 33
nom: "Avantage (AV) affiché"
specs:
  - specs/screens/tv-live.md
  - specs/screens/arbitre-match.md
modules:
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
tickets-tag: sprint-33
branche: claude/sprint/33-affichage-avantage
branche-parent: main
log: backlog/sprints/33-affichage-avantage/log.md
---

# Sprint 33 — Avantage (AV) affiché

**Objectif :** afficher l'avantage post 40/40 sur la TV et la tablette arbitre
en consommant `displayPointA/B` de `_pack_match` (suppression des deux mappings
locaux plafonnés à « 40 »), avec le signal broadcast sur la TV (AV en accent
côté avantagé).

> Origine : retours produit 2026-07-08 (problématique 1). Le moteur
> (`award_point_to`, écart de 2 points) et le packer (`tennis_point_display` →
> `displayPointA/B`) sont **corrects** — c'est une régression de portage front,
> dupliquée dans deux SFC. Aucun changement back.

## Définition de terminé

- Golden path : match LIVE amené à 40-40 ; point au joueur A → « AV – 40 »
  s'affiche sur la TV (AV en accent) **et** sur la tablette (sobre) ; point à
  B → retour « 40 – 40 » ; nouveau point à B → « 40 – AV » ; point gagnant →
  jeu incrémenté, points « 0 – 0 ». Sur la tablette, le comportement survit à
  un `swap` d'affichage.
- Tie-break : points bruts toujours affichés (le packer les renvoie déjà).
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur la partie « points » de [[tv-live]] et
  [[arbitre-match]].
- Aucune issue `sprint-33` ouverte.

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — points via `displayPointA/B`, signal broadcast AV
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — score central `0/15/30/40/AV`, affichage sobre

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 33 — Avantage (AV) affiché »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#321](https://github.com/sirius911/moutilloux/issues/321) | Front : TvScoreboard — points depuis displayPointA/B + signal broadcast AV | `TvScoreboard.vue` | |
| [#322](https://github.com/sirius911/moutilloux/issues/322) | Front : ArbitreMatch — score central depuis displayPointA/B | `ArbitreMatch.vue` | |

---

## Périmètre backend

Aucun.

## Fichiers partagés (orchestrateur uniquement)

Aucun.

## Ordre d'exécution suggéré

#321 ∥ #322 — fichiers disjoints, parallélisables (deux `vue-screen`).

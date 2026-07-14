---
type: transverse
module: affichage-participant
fichiers:
  - live/api_views.py
  - frontend/app/src/types/index.ts
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/tv/TvTicker.vue
  - frontend/app/src/views/tv/TvPalmares.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminBracket.vue
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
---

# Spec transverse — Affichage d'un participant

> Règle unique de nommage d'un **participant de match** (côté A / côté B),
> valable sur toutes les surfaces : TV, admin, arbitre, modales. Issue des
> retours du 2026-07-12 (« TBD vs TBD » au planning pour les équipes de
> Double, arbitrage : règle transverse + sweep).

## La règle

Toute mention d'un côté de match affiche, **par priorité décroissante** :

1. **`displayName`** de l'entrée assignée (`sideA.displayName` /
   `sideB.displayName`) — le seul champ qui couvre les deux modes :
   - épreuve **Simple** : « Nom Prénom » du joueur ;
   - épreuve **Double** : le **nom d'équipe** s'il existe, sinon
     « Joueur1 / Joueur2 » (construction serveur, `_entry_display_name`,
     `live/api_views.py:133`).
2. **L'étiquette de provenance** du slot (`sideALabel` / `sideBLabel`) —
   « A1 », « B2 », « Vainqueur SF1 », « LSF2 »… — quand la place n'est pas
   encore résolue.
3. **« À désigner »** — fallback unique de toute l'application. Les variantes
   (« TBD », placeholders anglophones) sont proscrites des surfaces
   utilisateur.

Le front ne reconstruit **jamais** un nom de participant depuis
`player.fullName` : ce champ ignore les équipes de Double et produit un
fallback erroné pour tout match de Double pourtant résolu.

## Implémentation front

- Un **helper partagé unique** (ex. `sideName(side, label?)` dans
  `frontend/app/src/utils/`) applique la règle ; toutes les SFC l'utilisent —
  aucune ré-implémentation locale de la chaîne de fallback.
- Contexte du sweep : au 2026-07-12, le motif fautif
  `side?.player?.fullName ?? sideLabel ?? fallback` apparaît ~55 fois dans
  10 fichiers (TV idle/ticker/palmarès/scoreboard, arbitre home/match,
  admin matchs/bracket/régie, panneau d'édition).

## Périmètre et exceptions

- La règle porte sur les **participants de match**. Les écrans qui manipulent
  des **joueurs** en tant que tels (fiches [[admin-joueurs]], inscriptions
  [[admin-inscriptions]], sélecteurs de la modale Équipe) continuent
  d'afficher l'identité du joueur (`fullName`) — c'est leur objet.
- Les écrans qui affichent les **membres** d'une équipe en plus du nom
  d'équipe (ex. affiche de match, [[affiche-match]]) le font en complément de
  `displayName`, pas à sa place.
- La bande scoreboard TV conserve sa formulation existante (« nom d'équipe en
  Double », [[tv-live]]) — c'est un cas particulier de la présente règle.

---
type: screen
module: arbitre/match
fichiers:
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/stores/live.ts
  - frontend/app/src/composables/usePolling.ts
  - frontend/app/src/composables/useScale.ts
  - frontend/app/src/composables/useApi.ts
  - live/referee_views.py
  - live/api_views.py
  - live/models.py
---

# Spec fonctionnelle — Saisie Arbitre (écran match)

## Rôle de l'écran

L'écran de saisie (`/arbitre/:matchId`) est le **poste de scoring** d'un match
unique, sur **iPad portrait (834 × 1112)**. Il est mis à l'échelle pour tenir sur
l'écran quel que soit l'appareil (scène fixe scalée, `useScale`). Il pilote la
rencontre point par point et **alimente en direct le scoreboard TV** ([[tv-live]]).

Le cycle de vie du match (états, transitions, qui peut quoi, forfait/abandon/annulation,
ré-ouverture) est décrit dans [[cycle-de-vie-match]] — cette spec en décrit l'**UI et
les flux**. Le match affiché est celui de l'URL (`:matchId`), poll via
`GET /api/matches/:id/` (et **non** le match « à l'antenne » global).

---

## Comportement selon l'état du match

L'écran a **trois modes**, dictés par `status` :

| État | Zones de tap | Action principale | Autres actions |
|---|---|---|---|
| `SCHEDULED` (PRÉVU) | **inactives** | **« Démarrer le match »** | Forfait, Annuler |
| `LIVE` (EN DIRECT) | **actives** (+ point) | saisie point par point | Annuler point, Corrections, Terminer |
| `FINISHED` (TERMINÉ) | inactives | — (retour) | *aucune* (ré-ouverture = admin seul) |

- **Démarrer** : ouvre le **modal de démarrage** (voir Flux : démarrer un match) —
  la première décision est **« Qui sert en premier ? »**, obligatoire avant que le
  match ne passe `LIVE`. À la confirmation, le match passe `LIVE` avec le serveur
  choisi et prend la mise en avant TV. Si **un autre match est déjà en cours**, le
  même modal l'annonce (« Un autre match est en cours — le démarrer le mettra en
  pause »), voir [[cycle-de-vie-match]]. Tant que le match est `SCHEDULED`, taper
  une zone de score ne fait rien (pas de scoring implicite : le match doit être
  démarré d'abord).
- **FINISHED** : l'écran est en **lecture seule**. Il montre le résultat (vainqueur,
  et le libellé « Forfait » / « Abandon » selon `end_reason`). L'arbitre **ne peut pas
  rouvrir** — s'il y a une erreur, il la signale à l'admin ([[cycle-de-vie-match]]).

---

## Éléments d'interface

### En-tête

- **Retour** (←) vers l'accueil ([[arbitre-home]]).
- **Étape + format** au centre : l'étape (« Poule A », « Quart »…) et un **libellé de
  format lisible** (« 1 set à 5 · TB à 4 »), pour que l'arbitre voie les règles qu'il
  applique (`formatLabel` dans `_pack_match` — voir [[cycle-de-vie-match]]).
- **Badge d'état** : EN COURS / JEU DÉCISIF (tie-break actif) / TERMINÉ.

### Bloc score

- **Joueur A** (gauche) et **Joueur B** (droite) : nom, **SETS n**, **JEUX n**, et un
  **indicateur de service** (●) du côté du serveur courant.
- **Score central** : le point du jeu en cours — `0 / 15 / 30 / 40` hors tie-break,
  **valeur numérique** en tie-break (avec le libellé « JEU DÉCISIF »).

### Zones de tap (le cœur de la saisie)

- Deux grandes zones plein écran, **une par joueur** (A à gauche, B à droite),
  libellées au nom du joueur, « + POINT », « TAP ICI ».
- Un tap = **un point** au joueur (`point_left` / `point_right`). Le moteur enchaîne
  automatiquement jeux → sets → tie-break, et **clôt le match sur le point gagnant**
  (fin automatique, voir [[cycle-de-vie-match]]).
- Zones **désactivées** (grisées) hors `LIVE`.

### Pied — actions

- **Annuler point** (`reset_points`) : remet le jeu en cours à 0-0 (rattrape un tap
  de trop). *(Comportement actuel : remet le point courant, pas un historique
  multi-coups — suffisant pour l'usage.)*
- **Corrections** : ouvre le **tiroir de corrections** (voir ci-dessous).
- **Terminer** : ouvre le **modal de fin** (voir Flux).

### Tiroir « Corrections »

Panneau repliable regroupant les ajustements manuels (toutes les actions back
**existent déjà** — pur câblage) :

- **Jeux ±** par côté (`game_left_plus/minus`, `game_right_plus/minus`) — refusé
  pendant un tie-break (message d'erreur du moteur).
- **Sets ±** par côté (`set_left_plus/minus`, `set_right_plus/minus`).
- **Changer le serveur** (`toggle_service`) : bascule qui sert. **Autorisé seulement
  à 0-0** du jeu (ou 0-0 du tie-break) — sinon le moteur renvoie une erreur affichée
  en toast.
- **Inverser les côtés** (`swap`) : intervertit l'**affichage** gauche/droite pour
  coller à la position physique de l'arbitre face au court. **N'affecte pas** le
  score ni qui sert — c'est un confort d'affichage (stocké en session).

> **`swap` ≠ `toggle_service`** : deux besoins distincts, deux boutons distincts
> (branchés séparément depuis le sprint 25, issue #283).

Le **format** du match est **affiché en lecture seule** dans ce tiroir ; le changer
appartient à l'admin (onglet Format, verrouillé quand le match est `LIVE` —
[[admin-matchs]]).

---

## Flux : démarrer un match (avec choix du premier serveur)

Ouvert par « Démarrer le match » (match `SCHEDULED`). Modal **« Démarrer le
match »** :

1. **« Qui sert en premier ? »** : deux boutons, un par joueur — **aucun n'est
   présélectionné** (la question doit être posée sur le court, pas héritée du
   format). Le bouton de confirmation reste désactivé tant qu'aucun serveur
   n'est choisi.
2. Si un **autre match est déjà `LIVE`**, le même modal porte l'avertissement
   « Un autre match est en cours — le démarrer le mettra en pause »
   ([[cycle-de-vie-match]]) : un seul geste, pas deux modales enchaînées.
3. **Confirmer** → `démarrer` avec le serveur choisi (contrat : l'action de
   démarrage porte un paramètre `server` A/B ; repère modèle, indépendant du
   `swap`). Le match passe `LIVE`, les zones de tap s'activent.
4. « Annuler » referme sans rien changer, le match reste `SCHEDULED`.

> **Cas hors parcours** : un match passé `LIVE` sans ce modal (mise en avant
> depuis l'admin, [[admin-matchs]]) garde le serveur de son format ; l'arbitre
> le corrige à 0-0 via le tiroir Corrections (`toggle_service`).

## Flux : Terminer (fin manuelle / abandon)

Ouvert par « Terminer ». Modal **« Déclarer vainqueur »** :

1. Deux boutons, un par joueur, avec un indice **« Mène »** sur celui en tête (déduit
   des sets/jeux courants).
2. Choisir le vainqueur → `terminer` avec `winner` (repère modèle A/B, indépendant du
   `swap`). Le match passe `FINISHED`, `end_reason = NORMAL`.
3. Une bascule **« Abandon adverse »** marque une fin par **retraite** (`end_reason =
   RETIREMENT`) : le score est **figé en l'état** (pas de complétion). Voir
   [[cycle-de-vie-match]].
4. « Annuler » referme sans rien changer.

> En jeu normal, la fin est **automatique** sur la balle de match ; ce modal sert aux
> **cas manuels** (abandon, score déjà décisif, litige).

## Flux : Forfait (walkover, match `SCHEDULED`)

Depuis un match non commencé : action **« Déclarer forfait »** → choisir le joueur
**présent** comme vainqueur → `forfait`. Le match passe `FINISHED`, `is_walkover`
(`end_reason = WALKOVER`), score de convention, et **reste à sa place** au calendrier
([[cycle-de-vie-match]], [[cycle-de-vie-epreuve]]).

## Flux : Annuler (double absence)

Action **« Annuler le match »** (confirmation, irréversible côté arbitre) →
`annuler`. Le match passe `CANCELED`, **sans vainqueur**, quitte le calendrier et
part en « Annulés » ([[admin-matchs]]). Exclu du classement.

## Flux : Réinitialiser

Action **« Reset »** (confirmation « action irréversible ») → `reset_all` : remet le
match à zéro (`SCHEDULED`, score effacé). À réserver aux vrais faux départs.

---

## Modales & retours

- **Modal de confirmation générique** (reset, annulation) : titre, corps « action
  irréversible » le cas échéant, « Annuler » / « Confirmer ».
- **Modal de démarrage** : choix obligatoire du premier serveur + avertissement
  si un autre match est en cours (voir Flux : démarrer un match).
- **Modal de fin** : sélection du vainqueur (voir Flux) + bascule abandon.
- **Toast d'erreur** : toute action **refusée par le moteur** renvoie une **erreur
  JSON** (`{ ok:false, error }`) que l'écran **affiche en toast** ~4 s. Exemples :
  changer le service en cours de jeu, ajouter un jeu pendant un tie-break, agir sur un
  match terminé. **C'est un cas de régression à tester** (golden path §6 CLAUDE.md).

---

## Données & temps réel

- Source : `GET /api/matches/:id/` (`_pack_match`), via `live.fetchMatch(id)` dans le
  store `live`. **Lecture publique** (le scoreboard TV consomme le même endpoint).
- **Rafraîchissement** ~2 s (`usePolling`). Après **chaque action**, l'écran
  **refait un fetch immédiat** (le moteur renvoie `{ok:true}` sans l'état) pour un
  retour instantané, sans attendre le tick suivant.
- **Pause onglet caché** : le polling se suspend onglet non visible (`usePolling`,
  `visibilitychange`).
- **Connectivité** : mode **en ligne** (v1). Si un tap échoue (réseau), l'action est
  **perdue** et l'erreur s'affiche — pas de file d'attente optimiste. Le prochain tick
  resynchronise l'état réel depuis le serveur. *(Une saisie hors-ligne avec rejeu est
  hors périmètre v1.)*

---

## États limites

| Situation | Comportement |
|---|---|
| Match introuvable / supprimé | Erreur de chargement ; retour possible vers l'accueil. |
| Joueurs non résolus (slot de tableau TBD) | Noms remplacés par les étiquettes ; le match ne devrait pas être démarrable tant que les deux joueurs ne sont pas connus. |
| Un autre match passe `LIVE` (démarré ailleurs) | Ce match, s'il était `LIVE`, repasse `SCHEDULED` au tick suivant (invariant mono-`LIVE`) ; l'écran le reflète. |
| Format `MANUAL` | Le moteur désactive la logique auto ; seules les corrections manuelles (jeux/sets) font foi. |

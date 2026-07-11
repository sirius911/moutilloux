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

L'écran a **quatre modes**, dictés par `status` et la phase du match
(voir [[cycle-de-vie-match]], « Échauffement ») :

| État | Zones de tap | Action principale | Autres actions |
|---|---|---|---|
| `SCHEDULED` (PRÉVU) | **inactives** | **« Démarrer le match »** (→ échauffement) | Forfait, Annuler |
| `LIVE` — **échauffement** (`playStartedAt` nul) | **inactives** | **« Lancer le match »** (choix du serveur) | Annuler, Reset |
| `LIVE` — **jeu** | **actives** (+ point) | saisie point par point | Annuler point, Corrections, Terminer |
| `FINISHED` (TERMINÉ) | inactives | — (retour) | *aucune* (ré-ouverture = admin seul) |

- **Démarrer** : passe **immédiatement** le match en **échauffement** — `LIVE`
  + `warmup_started_at`, mise en avant TV ([[tv-live]] affiche la scène
  échauffement). Si **un autre match est déjà en cours**, une confirmation
  l'annonce d'abord (« Un autre match est en cours — le démarrer le mettra en
  pause », voir [[cycle-de-vie-match]]). Il n'y a **plus de choix du serveur à
  ce stade**.
- **Échauffement** : l'écran affiche un **compte à rebours de 5 min**
  (constante, dérivé de `warmupStartedAt` — même source que la TV, donc
  synchronisé). Le timer est **indicatif** : à 0:00 rien ne se déclenche (le
  libellé passe à « prêt »). Taper une zone de score pendant l'échauffement ne
  fait rien (refusé par le moteur). Le bouton **« Lancer le match »** ouvre le
  modal « Qui sert en premier ? » (voir Flux) — le confirmer pose
  `play_started_at` et active les zones. **Pas de bouton « passer
  l'échauffement »** : lancer le match tôt le court-circuite naturellement.
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
- **Badge d'état** : ÉCHAUFFEMENT (avec le compte à rebours) / EN COURS /
  JEU DÉCISIF (tie-break actif) / TERMINÉ.

### Bloc score

- **Joueur A** (gauche) et **Joueur B** (droite) : nom, **SETS n**, **JEUX n**, et un
  **indicateur de service imposant** du côté du serveur courant : une **balle
  de tennis grand format** (même motif SVG que la TV, animée), doublée du
  **nom du serveur mis en avant** (accent) — qui sert doit se voir d'un coup
  d'œil (retours 2026-07-11). Valable sur les deux scènes (iPad et mobile).
- **Score central** : le point du jeu en cours — `0 / 15 / 30 / 40 / AV` hors
  tie-break (égalité affichée `40 / 40`), **valeur numérique** en tie-break (avec
  le libellé « JEU DÉCISIF »). L'affichage vient de **`displayPointA/B`** de
  `_pack_match` — le front **ne recalcule jamais** le libellé de point depuis les
  points bruts (la gestion deuce/avantage appartient au moteur).

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

## Flux : démarrer un match (entrée en échauffement)

Ouvert par « Démarrer le match » (match `SCHEDULED`) :

1. Si un **autre match est déjà `LIVE`**, une confirmation porte l'avertissement
   « Un autre match est en cours — le démarrer le mettra en pause »
   ([[cycle-de-vie-match]]). Sinon, l'action est directe (pas de modal).
2. Le match passe `LIVE` en **phase d'échauffement** (`warmup_started_at` posé,
   mise en avant TV). L'écran affiche le compte à rebours et le bouton
   « Lancer le match » ; les zones de tap restent inactives.
3. **Garde** : un match de tableau dont un slot n'est **pas résolu** (joueur
   inconnu) est refusé par le serveur (erreur JSON → toast), voir
   [[cycle-de-vie-match]].

## Flux : lancer le jeu (choix du premier serveur)

Ouvert par « Lancer le match » (match en échauffement). Modal **« Qui sert en
premier ? »** :

1. Deux boutons, un par joueur — **aucun n'est présélectionné** (la question
   doit être posée sur le court, pas héritée du format). Le bouton de
   confirmation reste désactivé tant qu'aucun serveur n'est choisi.
2. **Confirmer** → l'action de lancement porte un paramètre `server` A/B
   (repère modèle, indépendant du `swap`) et pose `play_started_at`. Les zones
   de tap s'activent, la TV bascule de la scène échauffement au scoreboard.
3. « Annuler » referme sans rien changer, le match reste en échauffement.

> **Cas hors parcours** : un match mis à l'antenne depuis l'admin
> ([[admin-matchs]]) suit la même mécanique dérivée — jamais lancé
> (`play_started_at` nul), il apparaît **en échauffement** et l'arbitre le lance
> par ce même modal ; **repris** après une mise en pause (`play_started_at` déjà
> posé), il revient **directement en jeu** (pas de ré-échauffement).

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

- **Modal de confirmation générique** (reset, annulation, démarrage quand un
  autre match est en cours) : titre, corps « action irréversible » le cas
  échéant, « Annuler » / « Confirmer ».
- **Modal de lancement** : choix obligatoire du premier serveur (voir Flux :
  lancer le jeu).
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
- **Étanchéité du polling** : l'écran n'affiche que le match de l'URL — une
  réponse tardive d'un autre match (navigation récente) est ignorée, et aucun
  timer de polling ne survit au démontage de l'écran (pas d'empilement
  d'intervalles ni de requêtes qui se chevauchent).
- **Connectivité** : mode **en ligne** (v1). Si un tap échoue (réseau), l'action est
  **perdue** et l'erreur s'affiche — pas de file d'attente optimiste. Le prochain tick
  resynchronise l'état réel depuis le serveur. *(Une saisie hors-ligne avec rejeu est
  hors périmètre v1.)*

---

## États limites

| Situation | Comportement |
|---|---|
| Match introuvable / supprimé | Erreur de chargement ; retour possible vers l'accueil. |
| Joueurs non résolus (slot de tableau TBD) | Noms remplacés par les étiquettes ; « Démarrer » est **refusé par le serveur** tant que les deux joueurs ne sont pas connus (erreur JSON → toast, garde décrite dans [[cycle-de-vie-match]]). |
| Un autre match passe `LIVE` (démarré ailleurs) | Ce match, s'il était `LIVE`, repasse `SCHEDULED` au tick suivant (invariant mono-`LIVE`) ; l'écran le reflète. |
| Format `MANUAL` | Le moteur désactive la logique auto ; seules les corrections manuelles (jeux/sets) font foi. |

---

## Variante mobile (téléphone)

L'écran a une **seconde scène fixe portrait** (~390 × 844) sélectionnée selon le
viewport, scalée par le même `useScale` — socle, sélection de scène, verrou
anti-tap et wake-lock décrits dans [[mobile]] :

- zones de tap empilées **haut / bas** (joueur du haut / joueur du bas, mêmes
  actions `point_left`/`point_right` re-mappées), score au centre ;
- actions secondaires (Corrections, Terminer, Forfait…) repliées dans un menu ;
- **verrou anti-tap** : un bouton cadenas gèle les zones (le téléphone vit dans
  une main ou une poche) ;
- comportements identiques à la scène iPad (mêmes modes, mêmes flux, mêmes
  erreurs) : seule la disposition change.

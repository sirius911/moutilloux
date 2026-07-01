---
type: screen
module: admin/tableau-final
fichiers:
  - frontend/app/src/views/admin/AdminBracket.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - live/bracket.py
---

# Spec fonctionnelle — Écran Tableau final

## Rôle de l'écran

L'écran Tableau final (`/admin/events/:eventId/bracket`) affiche et ajuste le
tableau de phase finale de l'**épreuve active**. Le squelette est créé au moment de
**« Débuter »** ; il se **peuple automatiquement** depuis les qualifiés des poules
(seeding positionnel à **séparation maximale**), avec **correction manuelle**
possible, et suit la progression automatique des gagnants jusqu'à la finale (voir
[[cycle-de-vie-epreuve]]).

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active,
  en lieu et place du fil d'ariane. Le **choix d'épreuve navigue** vers
  `/admin/events/:eventId/…` (`router.push`) ; l'URL fait foi et survit au
  rechargement (voir [[routing-context]]).
- Titre « Tableau final », sous-titre « Glissez les qualifiés dans les slots du bracket ».
- Quand un tableau existe : action secondaire **« Recréer le tableau »**.

### État initial (épreuve pas encore débutée)

- Le squelette est créé automatiquement par **« Débuter l'épreuve »** (voir
  [[cycle-de-vie-epreuve]]). En `INSCRIPTION`, l'écran invite à débuter l'épreuve
  depuis Tournoi. Il n'y a plus de création manuelle en temps normal (la forme du
  tableau suit le nombre de poules) ; **« Recréer le tableau »** reste un recours.

### Modale de recréation

Le squelette est normalement posé par **« Débuter »** ; sa forme (étape de départ,
byes) est **dérivée du nombre de poules et des qualifiés**, avec un seeding à
séparation maximale (voir [[cycle-de-vie-epreuve]]). La recréation manuelle est un
recours :

- la modale avertit : « Recréer le tableau efface les matchs planifiés actuels. »
  et demande confirmation ;
- règle serveur : recréation **refusée** si un match du tableau est déjà en direct
  ou terminé — le message d'erreur s'affiche dans la modale ;
- elle repose le **squelette** (places A/B étiquetées par provenance, sans
  participant assigné), prêt à se remplir au fil de l'eau.

### Le bracket

- Colonnes d'étapes : **Quarts** (si la forme du tableau le prévoit),
  **Demi-finales**, **Finale**, et **3e place** si l'épreuve l'active (voir
  [[cycle-de-vie-epreuve]]) ; chaque match identifié par son slot (QF1…, SF1, SF2,
  F1, P3).
- Chaque match expose deux **places** (côté A / côté B). Une place affiche, par
  priorité : le nom du participant assigné → l'étiquette de provenance
  (« A1 », « D2 »…) → « À désigner ».
- Le côté vainqueur d'un match terminé est mis en évidence.
- Une place occupée par un participant assignable porte un bouton ✕ pour la
  vider.
- Les étiquettes de provenance (« A1 », « C2 »…) sont **posées automatiquement**
  par le seeding (voir [[cycle-de-vie-epreuve]]). Chaque match **non commencé**
  permet de les **éditer** (champs courts) — c'est le **reseeding manuel** (forfait,
  arbitrage).

### Panneau « Qualifiés disponibles »

- Liste des qualifiés des poules : les participants classés dans les
  `qualified_per_group` premières places de chaque poule (au fil des résultats).
- Chaque entrée : pastille de provenance (« A1 », « B2 »…), nom, poignée de
  déplacement.
- Un qualifié **déjà placé** dans le tableau est affiché grisé avec la mention
  de sa place, et ne peut plus être déposé.
- État vide : « Aucun qualifié encore » (tant que les poules n'ont pas produit
  de classement).

---

## Flux : placement automatique et correction

1. **Automatique (au fil de l'eau)** : dès qu'une poule est classée, ses qualifiés
   sont **placés automatiquement** dans les slots selon le seeding positionnel à
   séparation maximale (voir [[cycle-de-vie-epreuve]]). L'écran reflète ces
   placements sans action de l'admin.
2. **Correction manuelle** : l'admin peut glisser un qualifié du panneau vers une
   place (côté A ou B), uniquement sur un match **non commencé** (statut Prévu) ;
   sinon le serveur refuse et le message exact est affiché.
3. La place affiche le participant ; le qualifié passe en « placé » dans le panneau.

## Flux : vider une place

1. L'admin clique ✕ sur une place occupée d'un match non commencé.
2. La place revient à son étiquette de provenance (ou « À désigner ») ; le
   qualifié redevient disponible.

## Flux : progression automatique

1. Quand un match du tableau se termine (saisie arbitre ou édition admin), le
   **gagnant est promu automatiquement** par le serveur dans la place
   correspondante de l'étape suivante. Si l'épreuve a une **petite finale**, les
   **perdants** des demies sont promus de même vers le match de 3e place (voir
   [[cycle-de-vie-epreuve]]).
2. L'écran reflète la progression sans action de l'admin, via son
   rafraîchissement périodique.
3. L'admin peut corriger une promotion en vidant la place du tour suivant tant
   que le match suivant n'a pas commencé.

---

## Gestion des erreurs

- Toute erreur (création, assignation, vidage) affiche **le message du
  serveur** dans une zone d'erreur visible de l'écran ou de la modale (`role:
  alert`), jamais un échec silencieux.
- Après une erreur de dépôt, le bracket est rechargé pour rester fidèle à
  l'état serveur.

## États limites

| Situation | Comportement |
|---|---|
| Aucune épreuve active | État vide avec lien vers Tournoi. |
| Poules non terminées | Le squelette existe (posé au Débuter) et est pré-étiqueté ; qualifiés et slots se remplissent au fil des résultats. |
| Tableau partiellement rempli | Les matchs incomplets restent « Prévus » ; ils ne peuvent pas être joués tant que leurs deux places ne sont pas assignées. |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/bracket`) : l'URL fait foi, le store la reflète, et un
  `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve.
- Bracket, poules et inscrits chargés au montage et au changement d'épreuve,
  rechargés après chaque mutation. L'écran se rafraîchit périodiquement (de
  l'ordre de quelques secondes) pour suivre la progression pendant la phase
  finale.

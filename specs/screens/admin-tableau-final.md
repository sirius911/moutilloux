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

L'écran Tableau final (`/admin/events/:eventId/bracket`) crée le tableau de phase finale de
l'**épreuve active**, le peuple depuis les qualifiés des poules (glisser-
déposer), pose les étiquettes de provenance des places, et suit la progression
automatique des gagnants jusqu'à la finale.

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active,
  en lieu et place du fil d'ariane. Le **choix d'épreuve navigue** vers
  `/admin/events/:eventId/…` (`router.push`) ; l'URL fait foi et survit au
  rechargement (voir [[routing-context]]).
- Titre « Tableau final », sous-titre « Glissez les qualifiés dans les slots du bracket ».
- Quand un tableau existe : action secondaire **« Recréer le tableau »**.

### État initial (aucun tableau)

- Message « Aucun tableau final créé pour cette épreuve. » + bouton principal
  **« Créer le tableau »** → modale de création.

### Modale de création / recréation

| Champ | Règle |
|---|---|
| Étape de départ | Quarts / Demi-finales / Finale. Présélection suggérée d'après le nombre de poules (≥ 4 poules → Quarts, sinon Demi-finales), modifiable. |

- En **recréation**, la modale avertit explicitement : « Recréer le tableau
  efface les matchs planifiés actuels. » et demande confirmation.
- Règle serveur : la recréation est **refusée** si un match du tableau est déjà
  en direct ou terminé — le message d'erreur s'affiche dans la modale.
- La création pose un **squelette vide** : les matchs de chaque étape existent
  (places A/B sans participant), à remplir à la main.

### Le bracket

- Trois colonnes d'étapes : **Quarts** (si l'étape de départ le prévoit),
  **Demi-finales**, **Finale**, chaque match identifié par son slot (QF1…, SF1,
  SF2, F).
- Chaque match expose deux **places** (côté A / côté B). Une place affiche, par
  priorité : le nom du participant assigné → l'étiquette de provenance
  (« A1 », « D2 »…) → « À désigner ».
- Le côté vainqueur d'un match terminé est mis en évidence.
- Une place occupée par un participant assignable porte un bouton ✕ pour la
  vider.
- Chaque match **non commencé** permet d'éditer ses deux étiquettes de
  provenance (champs courts « A1 », « D2 »…), pour documenter d'où viendront
  les joueurs avant leur qualification effective.

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

## Flux : assigner un qualifié

1. L'admin glisse un qualifié du panneau vers une place (côté A ou B) d'un
   match.
2. Règle : l'assignation n'est possible que sur un match **non commencé**
   (statut Prévu). Sinon le serveur refuse et le message exact est affiché.
3. La place affiche le participant ; le qualifié passe en « placé » dans le
   panneau.

## Flux : vider une place

1. L'admin clique ✕ sur une place occupée d'un match non commencé.
2. La place revient à son étiquette de provenance (ou « À désigner ») ; le
   qualifié redevient disponible.

## Flux : progression automatique

1. Quand un match du tableau se termine (saisie arbitre ou édition admin), le
   **gagnant est promu automatiquement** par le serveur dans la place
   correspondante de l'étape suivante.
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
| Poules non terminées | Le tableau peut être créé et pré-étiqueté ; le panneau des qualifiés se remplit au fil des résultats. |
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

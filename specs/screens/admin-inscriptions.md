---
type: screen
module: admin/inscriptions
fichiers:
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/components/modals/CreateTeamModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - competition/models.py
---

# Spec fonctionnelle — Écran Inscriptions

## Rôle de l'écran

L'écran Inscriptions (`/admin/events/:eventId/inscriptions`) rattache les joueurs du registre à
l'**épreuve active** : il crée et retire des inscriptions. En épreuve **Simple**,
on inscrit des joueurs individuels ; en épreuve **Double**, on inscrit des
équipes de deux joueurs.

L'écran dépend entièrement de l'épreuve active (sélecteur en en-tête de page) et
adapte son interface au mode de la catégorie (Simple / Double).

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active,
  en lieu et place du fil d'ariane. Le **choix d'épreuve navigue** vers
  `/admin/events/:eventId/…` (`router.push`) ; l'URL fait foi et survit au
  rechargement (voir [[routing-context]]).
- Titre « Inscriptions », sous-titre « N inscrit(s) ».
- Action principale selon le mode :
  - **Simple** : « Inscrire les N affichés » — inscrit en masse tous les joueurs
    actuellement visibles dans la liste « Joueurs disponibles » (donc en
    respectant la recherche en cours, et le libellé du bouton l'affiche).
    Désactivée si la liste affichée est vide ou pendant un traitement.
  - **Double** : « Créer une équipe » → modale Équipe.

### Carte « Inscrits »

Liste des participants de l'épreuve active :

| Colonne | Contenu |
|---|---|
| Participant | Avatar initiales + nom d'affichage (joueur, ou équipe : nom d'équipe sinon « Joueur1 / Joueur2 ») |
| Poule | Nom de la poule si le participant est affecté, sinon « — » |
| Actions | **Retirer** |

État vide : « Aucun inscrit pour cette épreuve ».

### Carte « Joueurs disponibles » (mode Simple uniquement)

- Joueurs du registre **non encore inscrits** à l'épreuve active, avec champ de
  recherche (nom complet).
- Chaque ligne propose **Inscrire**.
- État vide : « Tous les joueurs du registre sont inscrits ».

En mode **Double**, cette carte n'existe pas : l'ajout passe exclusivement par la
création d'équipe.

---

## Modale Équipe (mode Double)

Titre « Créer une équipe », sous-titre rappelant l'épreuve.

**Composition**
- Deux emplacements « Joueur 1 » et « Joueur 2 », chacun ouvrant un sélecteur
  avec recherche parmi les joueurs du registre.
- Les deux joueurs doivent être **différents** : un joueur choisi dans un
  emplacement est exclu de la liste de l'autre.

**Identification**
- Nom d'équipe optionnel (indication : « affiché sur la TV et l'écran arbitre ») ;
  sans nom, l'équipe s'affiche « Joueur1 / Joueur2 ».

**Comportement**
- Bouton « Créer l'équipe » désactivé tant que les deux joueurs ne sont pas
  choisis, et pendant la soumission.
- La création de l'équipe **inscrit automatiquement** l'équipe à l'épreuve
  active : à la fermeture, elle apparaît dans la carte Inscrits.
- Erreur serveur (épreuve non Double, joueurs identiques…) : message dans la
  modale, saisie conservée.

---

## Flux : inscrire un joueur (Simple)

1. L'admin clique « Inscrire » sur une ligne de Joueurs disponibles.
2. L'inscription est créée ; le joueur passe immédiatement de « disponibles » à
   « inscrits » ; les compteurs se mettent à jour.
3. Si l'épreuve n'est pas en mode Simple, le serveur refuse et le message
   s'affiche en bandeau d'erreur de l'écran.

## Flux : inscription en masse (Simple)

1. L'admin (éventuellement après avoir filtré par recherche) clique
   « Inscrire les N affichés ».
2. Tous les joueurs **affichés** sont inscrits en une opération. Les joueurs
   déjà inscrits entre-temps sont ignorés sans erreur.
3. La liste des inscrits se met à jour ; le bandeau d'erreur ne s'affiche que si
   l'opération entière échoue.

## Flux : retirer une inscription

1. L'admin clique « Retirer » sur un inscrit.
2. Une **modale de confirmation** s'affiche : « Retirer {nom} de l'épreuve ? » —
   avec le rappel que l'historique du joueur est conservé.
3. Règle serveur : le retrait est **refusé si le participant est déjà engagé
   dans au moins un match** de l'épreuve. Dans ce cas l'écran affiche le message
   d'erreur du serveur (« déjà utilisé dans un ou plusieurs matchs ») et la
   liste reste inchangée.
4. Sinon, l'inscription disparaît ; en Simple, le joueur réapparaît dans
   « Joueurs disponibles ».

---

## Gestion des erreurs

- Les erreurs d'action (inscription, retrait, équipe) affichent le message
  serveur dans un bandeau d'erreur en tête de contenu (ou dans la modale si
  l'action vient d'une modale). Le bandeau se vide à la prochaine action réussie.
- Pendant toute opération, les boutons d'action sont désactivés (pas de double
  soumission).

## États limites

| Situation | Comportement |
|---|---|
| Aucune épreuve active | L'écran affiche un état vide invitant à créer/sélectionner une épreuve (lien vers Tournoi) ; toutes les actions sont désactivées. |
| Registre vide | « Joueurs disponibles » vide avec lien vers l'écran Joueurs pour créer des fiches. |
| Épreuve passée de Simple à... | Sans objet : le mode d'une épreuve est porté par sa catégorie et ne change pas une fois des inscriptions créées (règle serveur, voir [[admin-tournoi]]). |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/inscriptions`) : l'URL fait foi, le store la reflète, et
  un `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve.
- Les listes (inscrits + registre) sont chargées au montage, rechargées au
  changement d'épreuve active et après chaque mutation réussie. Pas de polling.

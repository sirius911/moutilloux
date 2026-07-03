---
type: screen
module: admin/shell
fichiers:
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/router/index.ts
  - frontend/app/src/stores/event.ts
  - frontend/app/src/stores/auth.ts
  - live/api_views.py
---

# Spec fonctionnelle — Shell admin (layout + sidebar)

## Rôle de l'écran

Le shell admin est le cadre commun de tout l'espace `/admin/*`. Il fournit la barre
latérale (marque, navigation, liens de pied), héberge l'écran courant dans sa zone
principale, et porte l'**état global d'épreuve active** dont dépendent les écrans
Inscriptions, Poules, Planning et Tableau final. Le sélecteur d'épreuve est intégré
en en-tête de chacun de ces quatre écrans (décision 16).

L'espace admin est réservé à l'administrateur (superuser). Il s'affiche en thème
clair, cible PC 1440×900.

---

## Contrôle d'accès

| Situation | Comportement |
|---|---|
| Visiteur non authentifié sur `/admin/*` | Redirigé vers `/login` |
| Utilisateur authentifié non admin (ex. arbitre) | Redirigé vers `/arbitre` |
| Administrateur | Accès à toutes les routes `/admin/*` |

La garde s'applique à la route parente `/admin` **et couvre toutes ses routes
enfants**. `/admin` sans sous-chemin redirige vers `/admin/tournoi`.

---

## Éléments d'interface

### Sidebar — bloc marque

- Pastille logo + nom du tournoi (« MOUTILLOUX »).
- Sous-titre : libellé de l'édition active (ex. « Open · Édition 2026 »).
  Si aucune édition active n'existe, le sous-titre affiche un état neutre (« — »).

### Sidebar — navigation

Six entrées, dans cet ordre, chacune avec icône, libellé et compteur :

| Entrée | Route | Compteur affiché |
|---|---|---|
| Tournoi | `/admin/tournoi` | Nombre d'épreuves de l'édition active |
| Joueurs | `/admin/players` | Taille du registre de joueurs |
| Inscriptions | `/admin/events/:eventId/inscriptions` | Nombre d'inscrits de l'épreuve active |
| Poules | `/admin/events/:eventId/groups` | Nombre de poules de l'épreuve active |
| Planning | `/admin/events/:eventId/matches` | Nombre total de matchs de l'épreuve active |
| Tableau final | `/admin/events/:eventId/bracket` | Nombre de matchs du tableau (QF+SF+F) |

L'entrée **Planning** héberge l'écran dont le titre en zone principale est
« Calendrier des matchs » (voir [[admin-matchs]]) : le libellé court tient dans la
sidebar, le titre complet est porté par l'en-tête de l'écran (décision 17).

Les quatre entrées dépendantes d'une épreuve (Inscriptions, Poules, Planning,
Tableau final) pointent vers l'**épreuve active courante** : leur lien porte le
segment `:eventId` (décision 22, [[routing-context]]). Tournoi et Joueurs n'ont pas
de param d'épreuve.

Il n'y a pas d'écran Configuration : les catégories se créent inline depuis la
modale Épreuve (voir [[admin-tournoi]]) et le court unique est seedé en base.

- L'entrée correspondant à l'écran courant est mise en évidence (fond accent).
- Un compteur dont la donnée n'est pas encore chargée affiche un état neutre
  (vide), jamais « 0 » par défaut.

### Sidebar — pied

- **« Voir les résultats ↗ »** : ouvre l'affichage TV public (`/tv/live`) dans un
  nouvel onglet, sans quitter l'admin.
- **« Déconnexion »** : termine la session (requête de déconnexion protégée CSRF)
  puis redirige vers `/login`.

### Zone principale

Affiche l'écran de la route courante. Elle défile indépendamment de la sidebar,
qui reste fixe.

---

## Flux : changement d'épreuve

1. Depuis le sélecteur en en-tête d'un écran dépendant (Inscriptions, Poules,
   Planning, Tableau final), l'admin choisit une autre épreuve.
2. Le sélecteur **navigue** (`router.push`) vers le même écran avec le nouveau
   `:eventId` ; l'URL fait foi et l'état global se synchronise depuis elle
   (voir [[routing-context]]).
3. L'écran courant relance ses chargements pour la nouvelle épreuve et remplace
   son contenu. Le choix se **conserve d'un écran à l'autre** (les liens portent le
   `:eventId`) et **survit au rechargement**. Les écrans indépendants (Tournoi,
   Joueurs) ne sont pas affectés.
4. Les compteurs de navigation liés à l'épreuve se mettent à jour.

Aucune saisie en cours n'est perdue silencieusement : si une modale est ouverte,
elle reste ouverte (le sélecteur n'est pas accessible sous l'overlay d'une modale).

---

## Gestion des erreurs

- Échec du chargement des éditions/épreuves au montage : la sidebar affiche ses
  états neutres et l'écran courant son état d'erreur ou vide ; l'application ne
  casse pas.
- Session expirée (réponse 401 sur un appel) : l'utilisateur est renvoyé vers
  `/login` (règle transverse, voir [[erreurs-api]]).

---

## États limites

| Situation | Comportement |
|---|---|
| Aucune édition active | Sous-titre marque neutre, sélecteurs d'épreuve désactivés sur les écrans dépendants, ces écrans affichent leur état vide. L'écran Tournoi reste utilisable pour créer/activer une édition. |
| Édition active sans épreuve | Les sélecteurs affichent « Aucune épreuve » désactivé ; l'écran Tournoi propose la création d'épreuve. |
| Épreuve active supprimée (depuis Tournoi) | L'état global bascule sur la première épreuve restante, ou sur l'état « Aucune épreuve ». |

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
latérale (marque, sélecteur d'épreuve, navigation, liens de pied), héberge l'écran
courant dans sa zone principale, et porte le **contexte d'épreuve active** dont
dépendent les écrans Inscriptions, Poules, Matchs et Tableau final.

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

### Sidebar — sélecteur d'épreuve

- Libellé « ÉPREUVE » + liste déroulante des épreuves de l'édition active.
- La sélection définit l'**épreuve active**, contexte des écrans Inscriptions,
  Poules, Matchs et Tableau final.
- Par défaut, la première épreuve de l'édition est sélectionnée automatiquement
  dès que la liste est chargée.
- Changer d'épreuve recharge les données de l'écran courant pour la nouvelle
  épreuve, sans recharger la page.
- La sélection est conservée pendant toute la session de navigation (elle survit
  aux changements d'écran).
- S'il n'existe aucune épreuve, le sélecteur est désactivé et affiche
  « Aucune épreuve » ; les écrans dépendant de l'épreuve affichent leur état vide
  (voir leurs specs).

### Sidebar — navigation

Six entrées, dans cet ordre, chacune avec icône, libellé et compteur :

| Entrée | Route | Compteur affiché |
|---|---|---|
| Tournoi | `/admin/tournoi` | Nombre d'épreuves de l'édition active |
| Joueurs | `/admin/players` | Taille du registre de joueurs |
| Inscriptions | `/admin/inscriptions` | Nombre d'inscrits de l'épreuve active |
| Poules | `/admin/groups` | Nombre de poules de l'épreuve active |
| Matchs | `/admin/matches` | Nombre total de matchs de l'épreuve active |
| Tableau final | `/admin/bracket` | Nombre de matchs du tableau (QF+SF+F) |

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

1. L'admin choisit une épreuve dans le sélecteur.
2. L'épreuve active est mise à jour dans l'état global.
3. L'écran courant, s'il dépend de l'épreuve, relance ses chargements pour la
   nouvelle épreuve et remplace son contenu. Les écrans indépendants de l'épreuve
   (Tournoi, Joueurs) ne sont pas affectés.
4. Les compteurs de navigation liés à l'épreuve se mettent à jour.

Aucune saisie en cours n'est perdue silencieusement : si une modale est ouverte,
elle reste ouverte (le changement d'épreuve via la sidebar n'est pas accessible
sous l'overlay d'une modale).

---

## Gestion des erreurs

- Échec du chargement des éditions/épreuves au montage : la sidebar affiche ses
  états neutres et l'écran courant son état d'erreur ou vide ; l'application ne
  casse pas.
- Session expirée (réponse 401 sur un appel) : l'utilisateur est renvoyé vers
  `/login` (règle transverse, voir [[useapi-401]]).

---

## États limites

| Situation | Comportement |
|---|---|
| Aucune édition active | Sous-titre marque neutre, sélecteur vide désactivé, écrans d'épreuve en état vide. L'écran Tournoi reste utilisable pour créer/activer une édition. |
| Édition active sans épreuve | Sélecteur « Aucune épreuve » désactivé ; l'écran Tournoi propose la création d'épreuve. |
| Épreuve active supprimée (depuis Tournoi) | Le sélecteur bascule sur la première épreuve restante, ou sur l'état « Aucune épreuve ». |

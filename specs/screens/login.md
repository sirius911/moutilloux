---
type: screen
module: login
fichiers:
  - frontend/app/src/views/LoginView.vue
  - frontend/app/src/stores/auth.ts
  - frontend/app/src/stores/event.ts
  - frontend/app/src/router/index.ts
  - live/api_views.py
---

# Spec fonctionnelle — Page Login

## Rôle de la page

La page Login est le point d'entrée unique pour les utilisateurs authentifiés (Admin et Arbitre).
Elle permet également à tout visiteur d'accéder en lecture seule au tableau de bord en direct,
sans s'identifier. Elle n'a aucun formulaire d'inscription : les comptes sont créés par l'administrateur.

Il n'y a **pas de sélection de rôle** sur cette page : l'utilisateur saisit ses identifiants,
et le serveur détermine le rôle (admin, arbitre) à partir du profil du compte.

---

## Éléments d'interface

### Zone principale (formulaire)

**En-tête (brand)**
Nom du tournoi et **libellé de l'édition active**, affichés au-dessus du formulaire.
Si l'édition active n'est pas encore chargée, un état neutre est affiché (voir Comportement
des données contextuelles).

**Champ Nom d'utilisateur**
Champ texte obligatoire, toujours visible et saisissable.

**Champ Mot de passe**
Champ de saisie masquée, obligatoire, toujours visible et saisissable.

**Bouton "Se connecter"**
- Désactivé tant que les deux champs ne sont pas remplis (non vides).
- Actif dès que les deux champs sont remplis.
- En cours de traitement : le bouton se désactive et affiche un indicateur de chargement
  pour prévenir les doubles soumissions.

**Bouton "En direct"**
Lien public, toujours visible, qui permet d'accéder au tableau de bord TV sans s'authentifier.
Il est distinct du formulaire et clairement identifié comme accès spectateur.

### Zone secondaire (aside)

Panneau informatif affiché à côté du formulaire, visible sans interaction :
- Nombre d'**épreuves** rattachées à l'édition active

Cette donnée est indicative et affichée en lecture seule, sans interaction.

---

## Flux d'authentification

1. L'utilisateur saisit son nom d'utilisateur et son mot de passe.
2. Il soumet le formulaire (bouton "Se connecter" ou touche Entrée).
3. Une requête d'authentification est envoyée au serveur avec les identifiants fournis.
4. **En cas de succès :** le serveur établit une session et retourne le profil de l'utilisateur
   (statut admin, statut arbitre). L'application charge les informations du compte connecté,
   met à jour l'état global d'authentification, puis redirige vers l'écran approprié au rôle
   (voir Redirections).
5. **En cas d'échec :** aucune session n'est créée. Un message d'erreur est affiché dans le
   formulaire (voir Gestion des erreurs). Le nom d'utilisateur reste renseigné ; le mot de
   passe est effacé.

**Compte authentifié sans rôle.** Si les identifiants sont valides mais que le compte n'est
ni admin ni arbitre : le message "Compte non autorisé." est affiché dans le formulaire, et
l'application **déconnecte immédiatement la session** créée côté serveur (appel logout),
afin de ne laisser aucune session inutilisable ouverte. L'utilisateur peut retenter avec un
autre compte.

---

## Redirections

### Après connexion réussie

| Rôle reconnu | Destination par défaut |
|---|---|
| Admin | Tableau de bord d'administration du tournoi |
| Arbitre (non admin) | Accueil arbitre |

**Retour après login.** Si l'utilisateur a tenté d'accéder à une URL protégée avant de se
connecter, il est redirigé vers la page Login et la destination demandée est mémorisée.
Après connexion, la destination mémorisée est **validée avant redirection** :
- elle doit être un **chemin interne** à l'application (jamais une URL externe) ;
- elle doit être **permise au rôle** du compte connecté (un arbitre non admin n'est pas
  redirigé vers `/admin/...`).

Si la destination mémorisée est valide, l'utilisateur y est redirigé. Sinon (absente,
externe, ou non permise au rôle), il est redirigé vers la destination par défaut de son
rôle, sans rebond visible.

### Utilisateur déjà connecté

Si un utilisateur authentifié arrive sur la page Login (ex. en tapant l'URL directement),
il est immédiatement redirigé vers son écran par défaut, sans afficher le formulaire.

### Accès sans authentification

Le bouton "En direct" redirige vers le tableau de bord TV public, sans déclencher
de flux d'authentification.

---

## Gestion des erreurs

Règle commune à tous les échecs : le nom d'utilisateur reste renseigné, le **mot de passe
est effacé**, et le bouton "Se connecter" est réactivé (il redevient actif dès que le mot
de passe est ressaisi).

### Identifiants incorrects

Lorsque le serveur rejette les identifiants (nom d'utilisateur ou mot de passe erroné),
un message d'erreur s'affiche dans le formulaire, sous les champs de saisie ou en haut
du bloc formulaire. Le message est explicite et non technique : par exemple
"Identifiants incorrects. Vérifiez votre nom d'utilisateur et votre mot de passe."

### Erreur réseau ou serveur indisponible

Si la requête échoue sans réponse exploitable du serveur (timeout, perte de connexion,
erreur 5xx), un message générique s'affiche : "Une erreur est survenue. Veuillez réessayer."

### Compte non autorisé

Voir Flux d'authentification — message "Compte non autorisé." et déconnexion de la session.

### Aucune erreur de validation côté client

La page ne valide pas le format du nom d'utilisateur ni la complexité du mot de passe :
la vérification est entièrement déléguée au serveur. Côté client, seule la présence
(non-vide) des champs conditionne la possibilité de soumettre.

---

## Règles de validation (côté client)

| Condition | Comportement |
|---|---|
| Nom d'utilisateur vide | Soumission impossible |
| Mot de passe vide | Soumission impossible |
| Les deux champs remplis | Soumission possible |
| Soumission en cours | Soumission bloquée jusqu'à réponse du serveur |

Ces conditions s'appliquent à **toute voie de soumission** : clic sur le bouton
"Se connecter" comme validation par la touche Entrée dans un champ.

---

## Comportement des données contextuelles (en-tête et aside)

Le libellé de l'édition active (en-tête) et le nombre d'épreuves (aside) sont chargés au
montage de la page, de manière non bloquante. Si ces données ne sont pas encore disponibles,
un état neutre est affiché (vide ou squelette). Si le chargement échoue, ces zones restent
neutres sans message d'erreur visible — ces informations sont indicatives et ne bloquent
pas l'usage du formulaire.

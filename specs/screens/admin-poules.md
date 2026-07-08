---
type: screen
module: admin/poules
fichiers:
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/components/modals/AutoFillModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - competition/models.py
---

# Spec fonctionnelle — Écran Poules

## Rôle de l'écran

L'écran Poules (`/admin/events/:eventId/groups`) a **deux visages selon le statut de
l'épreuve** ([[cycle-de-vie-epreuve]]) :

- **`INSCRIPTION` — composition** : répartition automatique des inscrits,
  ajustements manuels par glisser-déposer, création/suppression de poules.
- **`EN_COURS` / `TERMINÉE` — suivi** : la composition est verrouillée et chaque
  poule affiche son **classement** et les **résultats de ses matchs** — c'est la
  vue « où en est cette poule » de l'admin.

Ni la génération des matchs ni le verrouillage ne se déclenchent ici : ils sont
l'effet de **« Débuter l'épreuve »** sur l'écran Tournoi (voir
[[cycle-de-vie-epreuve]]). Une fois l'épreuve débutée, seuls des **ajustements
ponctuels** (forfait, remplacement, ajout tardif, retrait) restent possibles.

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active,
  en lieu et place du fil d'ariane. Le **choix d'épreuve navigue** vers
  `/admin/events/:eventId/…` (`router.push`) ; l'URL fait foi et survit au
  rechargement (voir [[routing-context]]).
- Titre « Poules », sous-titre « Glissez-déposez les joueurs dans leur groupe ».
- Actions :
  - **« + Nouvelle poule »** → crée une poule **vide** (lettre suivante : A, B,
    C…) sans passer par le remplissage automatique. Permet de composer entièrement
    à la main (créer les poules vides puis glisser-déposer les joueurs).
    Désactivée quand les poules sont verrouillées.
  - **« Remplir automatiquement »** → modale de remplissage. Désactivée quand les
    poules sont verrouillées.

### Colonne « Non assignés »

- Liste des inscrits sans poule, chacun en pastille déplaçable (poignée ⋮⋮,
  avatar, nom).
- C'est aussi une zone de dépôt : y déposer un joueur le retire de sa poule.
- État « tout placé » : coche + « Tous les joueurs sont placés ».

### Grille des poules

Une carte par poule :
- En-tête : lettre de la poule sur pastille accent, « Poule {X} », nombre de
  joueurs, et (en `INSCRIPTION`) l'action **Supprimer la poule** (voir Flux).
- Liste des membres en pastilles déplaçables ; un badge **Q** marque les
  participants **qualifiés** — affiché **seulement une fois la poule terminée**
  (aucun Q sur classement partiel, voir [[cycle-de-vie-epreuve]]), avec un
  libellé au survol : « Qualifié pour le tableau final ».
- Bouton ✕ par pastille : retire le joueur de la poule (équivalent au dépôt sur
  « Non assignés »).
- Zone de dépôt vide : « Glissez un joueur ici ».

### Suivi de poule (épreuve débutée)

Dès que l'épreuve est `EN_COURS`, chaque carte de poule s'enrichit — mêmes
données que la slide Poules de la TV ([[tv-live]]) plus le détail des matchs :

- **Classement** : tableau rang / participant / V-D / points (source :
  [[classement-poule]]), badge **Q** sur les qualifiés une fois la poule
  terminée.
- **Matchs de la poule** : chaque rencontre avec son état — score final et
  vainqueur en évidence (`FINISHED`, libellé « Forfait » si walkover), « en
  cours » (`LIVE`, score courant), « à venir » (`SCHEDULED`, ~heure estimée si
  planifié), « annulé » (`CANCELED`, atténué).
- Une **légende** en pied de grille rappelle le sens du badge Q et des états.

### Bandeau de verrouillage

Dès que l'**épreuve est débutée** (`status = EN_COURS`, voir
[[cycle-de-vie-epreuve]]), la composition passe en lecture seule et l'écran
bascule en mode **suivi** (voir « Suivi de poule ») :
- un bandeau explique : « L'épreuve est débutée — la composition des poules est
  verrouillée », avec un lien vers l'écran Calendrier ;
- le glisser-déposer de **recomposition** est désactivé (pastilles non déplaçables,
  ✕ masqués) ;
- « Remplir automatiquement », « + Nouvelle poule » et « Supprimer la poule »
  sont désactivés ;
- restent accessibles les **ajustements ponctuels** de [[cycle-de-vie-epreuve]]
  (déclarer un forfait, remplacer ou retirer un joueur, ajouter un inscrit tardif
  dans une poule sous l'effectif).

---

## Modale « Remplir automatiquement »

Titre « Remplir les poules automatiquement ».

**Champs**

| Champ | Règle |
|---|---|
| Joueurs par poule | 3 ou 4 (segmenté, défaut : la taille par défaut de l'épreuve) |
| Méthode de répartition | « Ordre d'inscription » ou « Aléatoire » |

**Prévisualisation**
- Calcul affiché en direct : nombre de poules résultant (= ⌈inscrits / taille⌉)
  et effectif de chacune (répartition la plus équilibrée possible), sous forme de
  pastilles « Poule A · n joueurs ».

**Avertissement**
- Encadré visible : « Les compositions existantes seront réinitialisées si vous
  confirmez. » (le remplissage repart de zéro : il vide les poules puis répartit
  **tous** les inscrits).

**Comportement**
- Bouton de confirmation libellé avec le résultat (« Générer N poules de T »).
- Refus serveur si l'épreuve n'a aucun inscrit : message dans la modale.
- À la réussite : la modale se ferme, la grille affiche les nouvelles poules
  (créées A, B, C… selon le besoin), « Non assignés » est vide.

---

## Flux : créer une poule à la main

1. Tant que l'épreuve n'est pas débutée, l'admin clique **« + Nouvelle poule »**.
2. Une poule vide apparaît dans la grille (lettre = première lettre libre A, B,
   C…), avec sa zone de dépôt « Glissez un joueur ici ».
3. L'admin répartit les inscrits par glisser-déposer (voir flux suivant). Aucune
   génération de matchs ni verrouillage n'est déclenché : la composition reste
   libre jusqu'à « Débuter l'épreuve » (écran Tournoi).

## Flux : supprimer une poule

1. Tant que l'épreuve est en `INSCRIPTION`, chaque carte de poule porte une
   action **Supprimer la poule**.
2. Poule **vide** : suppression immédiate après confirmation simple. Poule
   **avec membres** : la confirmation précise que les joueurs seront renvoyés
   vers « Non assignés » (aucune inscription n'est supprimée).
3. À la confirmation : la poule disparaît, ses membres réapparaissent dans
   « Non assignés ». Pas de renumérotation des autres poules — la lettre
   libérée sera réutilisée par la prochaine création (« première lettre
   libre », voir Flux : créer une poule à la main).
4. Règle serveur : suppression **refusée** dès que l'épreuve est débutée
   (`EN_COURS`) — le message d'erreur est affiché en bandeau.

## Flux : déplacement manuel

1. L'admin saisit une pastille (depuis « Non assignés » ou une poule) et la
   dépose sur une poule cible.
2. Le participant est affecté à la poule cible (et retiré de sa poule
   précédente le cas échéant). L'interface reflète le changement immédiatement.
3. Déposer sur « Non assignés » (ou cliquer ✕) retire le participant de sa
   poule.
4. Si le serveur refuse (poules verrouillées entre-temps), le message d'erreur
   exact est affiché en bandeau et l'affichage est resynchronisé avec l'état
   serveur.

---

## Gestion des erreurs

- Toute erreur d'affectation ou de remplissage affiche le **message du
  serveur** (pas un texte générique) en bandeau d'erreur de l'écran ou dans la
  modale.
- Après une erreur de dépôt, les listes sont rechargées pour éviter tout état
  visuel mensonger.

## États limites

| Situation | Comportement |
|---|---|
| Aucune épreuve active | État vide avec lien vers Tournoi. |
| Aucun inscrit | « Non assignés » vide + invite à passer par l'écran Inscriptions ; « Remplir automatiquement » désactivé. |
| Aucune poule encore créée | Seule la colonne « Non assignés » est peuplée. Deux voies pour créer des poules : **« + Nouvelle poule »** (poules vides à composer à la main par glisser-déposer) ou **« Remplir automatiquement »** (création + répartition en un geste). |
| Poules verrouillées | Bandeau + lecture seule (voir ci-dessus). |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/groups`) : l'URL fait foi, le store la reflète, et un
  `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve.
- Inscrits et poules chargés au montage et au changement d'épreuve active,
  rechargés après chaque mutation. L'état de verrouillage est déduit du **statut de
  l'épreuve** (`EN_COURS`, voir [[cycle-de-vie-epreuve]]).
- Pas de polling en mode composition. En mode **suivi** (épreuve `EN_COURS`),
  rafraîchissement périodique (~5 s, `usePolling`) pour suivre scores et
  classements en direct.

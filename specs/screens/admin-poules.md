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

L'écran Poules (`/admin/events/:eventId/groups`) compose les poules de l'**épreuve active** :
répartition automatique des inscrits, ajustements manuels par glisser-déposer.
La composition est libre **tant que l'épreuve n'est pas débutée** ; elle est
ensuite verrouillée.

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
- Action principale : **« Remplir automatiquement »** → modale de remplissage.
  Désactivée quand les poules sont verrouillées.

### Colonne « Non assignés »

- Liste des inscrits sans poule, chacun en pastille déplaçable (poignée ⋮⋮,
  avatar, nom).
- C'est aussi une zone de dépôt : y déposer un joueur le retire de sa poule.
- État « tout placé » : coche + « Tous les joueurs sont placés ».

### Grille des poules

Une carte par poule :
- En-tête : lettre de la poule sur pastille accent, « Poule {X} », nombre de
  joueurs.
- Liste des membres en pastilles déplaçables ; un badge **Q** marque les
  participants qualifiés (selon les classements une fois les résultats connus).
- Bouton ✕ par pastille : retire le joueur de la poule (équivalent au dépôt sur
  « Non assignés »).
- Zone de dépôt vide : « Glissez un joueur ici ».

### Bandeau de verrouillage

Dès que l'**épreuve est débutée** (`status = EN_COURS`, voir
[[cycle-de-vie-epreuve]]), l'écran passe en lecture seule :
- un bandeau explique : « L'épreuve est débutée — la composition des poules est
  verrouillée », avec un lien vers l'écran Calendrier ;
- le glisser-déposer de **recomposition** est désactivé (pastilles non déplaçables,
  ✕ masqués) ;
- « Remplir automatiquement » est désactivé ;
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
| Aucune poule encore créée | Seule la colonne « Non assignés » est peuplée ; le remplissage automatique crée les poules. |
| Poules verrouillées | Bandeau + lecture seule (voir ci-dessus). |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/groups`) : l'URL fait foi, le store la reflète, et un
  `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve.
- Inscrits et poules chargés au montage et au changement d'épreuve active,
  rechargés après chaque mutation. L'état de verrouillage est déduit du **statut de
  l'épreuve** (`EN_COURS`, voir [[cycle-de-vie-epreuve]]). Pas de polling.

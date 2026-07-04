---
type: screen
module: admin/tournoi
fichiers:
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/components/modals/EditionModal.vue
  - frontend/app/src/components/modals/EventModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - core/models.py
---

# Spec fonctionnelle — Écran Tournoi

## Rôle de l'écran

L'écran Tournoi (`/admin/tournoi`, écran par défaut de l'espace admin) est le
tableau de bord de l'**édition active** et le lieu de gestion du cycle de vie des
**éditions** et des **épreuves**. C'est ici que démarre une nouvelle année de
tournoi et que l'on configure ce qui sera joué.

Deux notions distinctes y cohabitent, avec un vocabulaire strict :
- **Activer** une édition : bascule globale et persistée — toute l'application
  (admin, arbitre, TV) travaille sur cette édition.
- **Sélectionner** une épreuve : choix d'affichage **porté par l'URL** (segment
  `/admin/events/:eventId/…`) qui définit l'épreuve active des écrans Inscriptions /
  Poules / Planning / Tableau final ; il survit au rechargement et au partage de
  lien (décision 22, voir [[routing-context]]).

---

## Éléments d'interface

### En-tête de page

- Fil d'ariane « Administration », titre « Tournoi », sous-titre
  « Vue d'ensemble de l'édition active ».
- Action principale : **« + Nouvelle édition »** → ouvre la modale Édition en
  mode création.

### Carte « Édition active »

- Titre : pastille active + « Édition active · {nom} {année} ». Si aucune édition
  active : la carte affiche un état vide invitant à créer ou activer une édition.
- Période : dates de début et de fin de l'édition si renseignées (« 25 mai →
  02 juin 2026 »), sinon rien.
- **Statistiques de l'édition** (toutes épreuves confondues) :

| Stat | Définition |
|---|---|
| Joueurs inscrits | Nombre de joueurs distincts inscrits à au moins une épreuve de l'édition (les deux membres d'une équipe comptent chacun) |
| Épreuves | Nombre d'épreuves de l'édition |
| Matchs joués | Nombre de matchs terminés / nombre total de matchs, toutes épreuves de l'édition |

### Carte « Épreuves de l'édition »

- Action : **« + Nouvelle épreuve »** → ouvre la modale Épreuve en mode création.
  Désactivée s'il n'y a pas d'édition active.
- Une carte par épreuve, affichant :
  - badge de mode (S / D) et nom de la catégorie ;
  - configuration : taille de poule par défaut et nombre de qualifiés par poule
    (ex. « Poules de 4 · 2 qualifiés ») ;
  - nombre d'inscrits ;
  - **badge d'avancement** dérivé du **statut de l'épreuve** (voir
    [[cycle-de-vie-epreuve]]) : « À préparer » / « Inscription » (`INSCRIPTION`),
    « Poules » / « Phase finale » (`EN_COURS`), « Terminée » (`TERMINÉE`) ;
  - raccourcis **Inscriptions**, **Poules**, **Matchs** : sélectionnent l'épreuve
    puis naviguent vers l'écran correspondant ;
  - **Débuter** (si `status = INSCRIPTION`) → lance la phase de jeu : génère les
    matchs de poule, verrouille la composition, crée le squelette du tableau, ouvre
    la planification (confirmation avec aperçu — voir Flux et
    [[cycle-de-vie-epreuve]]). **Rouvrir** (si `status = TERMINÉE`) → repasse
    l'épreuve en jeu pour corriger un résultat.
  - **Modifier** → modale Épreuve en mode édition ;
  - **Supprimer** → confirmation forte (voir Flux) ;
  - Pas de bouton « Sélectionner » dédié : la sélection de l'épreuve est portée
    par la navigation elle-même (raccourcis Inscriptions/Poules/Matchs
    ci-dessus), cohérent avec le principe « sélection portée par l'URL »
    énoncé en introduction (décision 22, [[routing-context]]).
- État vide : « Aucune épreuve créée pour cette édition. »

### Carte « Historique des éditions »

Tableau de **toutes** les éditions (active et archivées), triées de la plus
récente à la plus ancienne :

| Colonne | Contenu |
|---|---|
| Édition | Avatar année + nom + mention « Édition active » ou « Archive » |
| Année | Année (unique) |
| Dates | « début → fin » ou « — » |
| Épreuves | Nombre d'épreuves de l'édition |
| Statut | Pastille « En cours » (active) ou « Terminée » |
| Actions | **Activer** (désactivé sur l'édition déjà active, libellé « Active ✓ »), **Modifier**, **Supprimer** |

État vide : « Aucune édition dans l'historique. »

---

## Modale Édition (création / édition)

**Champs**

| Champ | Règle |
|---|---|
| Nom | Requis (texte libre, ex. « Open de Moutilloux 2026 ») |
| Année | Requise, entier ; **unique** parmi les éditions |
| Date de début | Optionnelle |
| Date de fin | Optionnelle |
| Durée de match par défaut (min) | Optionnelle, entier ≥ 1 (défaut 27) ; sert de base au moteur d'ETA du calendrier |

**Comportement**
- Le bouton d'enregistrement est désactivé tant que nom ou année sont vides,
  et pendant la soumission.
- **Activation automatique** : une édition créée alors qu'**aucune édition
  active n'existe** devient active immédiatement (cas du premier lancement).
  Sinon, elle naît **en préparation** (archive) : on l'active explicitement
  depuis l'historique quand on veut basculer l'application dessus. Il n'y a
  pas de case « Activer immédiatement ».
- En cas d'année déjà utilisée, le serveur refuse : la modale affiche le message
  d'erreur et reste ouverte, valeurs conservées.
- À la réussite : la modale se ferme, l'historique et (le cas échéant) la carte
  Édition active se mettent à jour.

## Modale Épreuve (création / édition)

**Champs**

| Champ | Règle |
|---|---|
| Catégorie | Requise en création — sélecteur des catégories existantes **avec création inline** (voir ci-dessous). **Non modifiable en édition** (l'identité d'une épreuve est édition × catégorie). |
| Joueurs par poule | 3 ou 4 (défaut 4) |
| Qualifiés par poule | 1 ou 2 (défaut 2) |
| Petite finale | Optionnel — match pour la 3e place (perdants des demies). Défaut : non. Voir [[cycle-de-vie-epreuve]]. |
| Notes | Texte libre optionnel |

**Création de catégorie inline**
- Le sélecteur de catégorie propose une entrée **« + Nouvelle catégorie »** qui
  déplie deux champs dans la modale : Nom (requis, **unique**, comparaison
  insensible à la casse) et Mode (Simple / Double, segmenté).
- La catégorie est créée en même temps que l'épreuve (ou à la volée avant la
  soumission) ; en cas de nom en doublon, le serveur refuse et le message
  s'affiche dans la modale, saisie conservée.
- C'est le **seul point de création** de catégorie dans l'UI. Renommage et
  suppression (rares) passent par l'admin Django, filet de sécurité technique.
  Règle serveur conservée : le mode d'une catégorie ne peut plus changer dès
  qu'une inscription existe sur une épreuve de cette catégorie.

**Comportement**
- Une catégorie déjà utilisée par une épreuve de la même édition est refusée par
  le serveur : message d'erreur explicite dans la modale.
- **Avertissement de cohérence** : si l'épreuve a déjà des poules ou un tableau,
  la modale d'édition affiche un avertissement avant enregistrement — modifier le
  nombre de qualifiés (en particulier le passer sous 2) peut casser le
  remplissage automatique du tableau final.

---

## Flux : activer une édition

1. L'admin clique « Activer » sur une édition de l'historique.
2. L'édition devient active ; **toutes les autres sont automatiquement
   désactivées** (règle serveur, une seule édition active à la fois).
3. L'interface entière bascule : carte Édition active, sous-titre de la sidebar,
   sélecteur d'épreuve (repeuplé avec les épreuves de la nouvelle édition,
   première épreuve sélectionnée), statuts de l'historique.

## Flux : supprimer une édition

1. L'admin clique « Supprimer ».
2. Une **modale de confirmation** s'affiche (pas de dialogue natif du
   navigateur), rappelant le nom et l'année.
3. Règle : la suppression n'est possible que si l'édition est **vide**
   (0 épreuve). Sinon, le serveur refuse et l'écran affiche le message d'erreur,
   en suggérant de supprimer d'abord les épreuves — ou de simplement laisser
   l'édition en archive.

## Flux : supprimer une épreuve

1. L'admin clique « Supprimer » sur une carte d'épreuve.
2. Modale de confirmation forte : elle énonce explicitement que la suppression
   efface **inscriptions, poules, matchs et tableau** de l'épreuve.
3. Règle serveur : refusée si l'épreuve contient des matchs en cours ou terminés ;
   le message d'erreur est affiché tel quel.
4. Si l'épreuve supprimée était l'épreuve active, la sélection bascule (voir spec
   [[admin-shell]]).

## Flux : débuter / clôturer une épreuve

1. Sur une épreuve `INSCRIPTION`, l'admin clique **« Débuter »**.
2. Une **modale de confirmation** affiche l'aperçu du round-robin (matchs créés par
   poule) et avertit si des inscrits ne sont pas placés (ils seront **exclus** tant
   qu'on ne les rajoute pas — voir ajustements dans [[cycle-de-vie-epreuve]]).
3. À la confirmation : matchs de poule générés, composition **verrouillée**,
   squelette du tableau créé, planification ouverte, et l'épreuve passe
   **`EN_COURS`**. Mécanique complète : [[cycle-de-vie-epreuve]].
4. La **clôture** est **automatique** quand la finale est jouée (`→ TERMINÉE`) ;
   « Rouvrir » est une action d'urgence pour corriger après coup.

---

## Gestion des erreurs

- Toute erreur de mutation (activation, suppression, création) affiche le message
  d'erreur renvoyé par le serveur dans une zone d'erreur visible de l'écran ou de
  la modale concernée — jamais d'échec silencieux.
- Les erreurs de validation de formulaire restent dans la modale, champs
  conservés.

## Données

- Les données de l'écran sont chargées au montage et rechargées après chaque
  mutation réussie (pas de polling sur cet écran).

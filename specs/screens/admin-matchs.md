---
type: screen
module: admin/matchs
fichiers:
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/components/modals/GenerateMatchesModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - live/models.py
---

# Spec fonctionnelle — Écran Matchs

## Rôle de l'écran

L'écran Matchs (`/admin/matches`) pilote le flux des matchs de l'**épreuve
active** : génération des matchs de poule, ordonnancement de la file d'attente,
édition fine d'un match, et mise en avant du match diffusé sur la TV.

C'est un kanban à trois colonnes : **Backlog** (matchs à planifier), **File
d'attente** (ordre de passage), **Terminés**.

---

## Éléments d'interface

### En-tête de page

- Fil d'ariane « Tournoi · {épreuve} », titre « Matchs », sous-titre « Backlog,
  file d'attente et matchs terminés ».
- Action principale : **« Générer les matchs de poule »** → modale de
  génération.

### Colonnes du kanban

| Colonne | Contenu | Tri |
|---|---|---|
| **Backlog** | Matchs planifiés (`SCHEDULED`) sans position dans la file | Par étape puis id |
| **File d'attente** | En tête : le match **EN DIRECT** s'il existe (non déplaçable, badge « EN DIRECT » / « ★ EN AVANT ») ; puis les matchs planifiés ordonnés (position 1 = prochain à passer) | Position de file |
| **Terminés** | Matchs terminés, et matchs annulés avec badge « ANNULÉ » | Plus récent en premier |

### Carte de match

- Étiquette d'étape : « POULE {X} », « QUART », « DEMI », « FINALE ».
- Les deux participants (« {A} vs {B} ») — nom du participant, ou étiquette de
  provenance (« A1 », « D2 »), ou « À désigner ».
- Métadonnées selon l'état : court et heure prévue (file), score final
  (terminés).
- Badge « ★ EN AVANT » sur le match mis en avant.
- Poignée de déplacement (⋮⋮) sur les cartes déplaçables (backlog et file,
  hors match en direct).
- Bouton **« ★ Mettre en avant »** sur les cartes de la **file** qui ne sont pas
  déjà en avant. Ce bouton n'ouvre pas le panneau d'édition (clic indépendant
  du clic carte).
- Cliquer la carte ouvre le **panneau d'édition** du match.

---

## Modale « Générer les matchs de poule »

- Sous-titre : « Round-robin complet pour chaque poule. »
- Tableau de répartition : pour chaque poule — lettre, nombre de joueurs, nombre
  de matchs à créer (n·(n−1)/2) ; ligne Total.
- Le format de match appliqué est le **format de poule par défaut** (1 set à 5
  jeux, tie-break à 4-4) ; la modale l'indique en clair. Il reste ajustable
  ensuite match par match via le panneau d'édition.
- Bouton de confirmation : « Générer N matchs ».
- La génération est **idempotente** : les rencontres déjà créées ne sont pas
  dupliquées ; relancer la génération ne crée que les paires manquantes. La
  réponse indique le nombre réellement créé, affiché en retour (« N matchs
  créés »).
- Cas limites : aucune poule ou poules à moins de 2 participants → la modale
  l'indique (0 match à créer) et la confirmation est désactivée.
- Après génération, les nouveaux matchs apparaissent dans le **Backlog**, et la
  composition des poules devient verrouillée (voir [[admin-poules]]).

---

## Flux : ordonnancer la file

1. L'admin glisse une carte du Backlog vers la File (à la position voulue), ou
   réordonne les cartes de la File entre elles, ou sort une carte de la File
   vers le Backlog.
2. Le nouvel ordre complet de la file est envoyé au serveur ; les positions
   sont réattribuées (1..N). Un match sorti de la file perd sa position.
3. Un match entrant en file **reçoit automatiquement le court unique** (seedé
   en base — contexte mono-court, voir le journal de [[admin-panel-map]]) s'il
   n'en a pas déjà.
4. Le match en direct ne fait pas partie de l'ordre (il est déjà sorti de la
   file) ; il reste affiché en tête de colonne.

## Flux : mettre un match en avant

1. L'admin clique « ★ Mettre en avant » sur un match de la file.
2. Une **confirmation** explicite l'effet : « Ce match passe EN DIRECT et
   devient le match affiché sur la TV. Le match actuellement à l'antenne est
   retiré. »
3. À la confirmation : le match devient LIVE, sort de la file, prend le badge
   « EN AVANT » en tête de file ; l'éventuel match précédemment en avant perd
   son statut de diffusion.

---

## Panneau d'édition de match (volet latéral)

Ouvert au clic sur une carte. En-tête : étape, « {A} vs {B} », badges d'état
(PRÉVU / EN DIRECT / TERMINÉ / ANNULÉ), court, heure, « ★ MIS EN AVANT ».
Trois onglets : **Score**, **Format**, **Planning**. Pied : « Annuler » et
« Enregistrer » (désactivé pendant la sauvegarde ; les erreurs s'affichent dans
le pied sans fermer le panneau).

### Onglet Score

- Mention : « éditable en cas d'erreur arbitre » — la saisie normale du score se
  fait sur l'écran Arbitre ; cet onglet sert aux **corrections**.
- Grille par joueur : sets gagnés, jeux du set en cours, points du jeu en cours.
- Interrupteur « Tie-break activé » (quand il est désactivé, les points de
  tie-break sont remis à zéro).
- Sélecteur **Vainqueur** : « À déterminer » / {A} / {B}.
- Les valeurs saisies sont enregistrées telles quelles (pas de recalcul
  automatique) ; les valeurs négatives sont ramenées à zéro.

### Onglet Format

- Préréglage de format : « Poule : 1 set à 5, TB à 4-4 », « Quart : 1 set à 6,
  TB à 5-5 », « Demi : 1 set normal », « Finale : 2 sets gagnants », « Manuel ».
  Choisir un préréglage applique ses règles ; « Manuel » laisse les règles
  détaillées libres.
- Règles détaillées : jeux pour gagner le set, seuil de tie-break, sets gagnants
  (best of), points du tie-break, tie-break à 2 points d'écart, mode du set
  décisif (set complet / super tie-break) et points du super tie-break.
- Service initial : {A} / {B}.
- **Verrouillage** : quand le match est EN DIRECT, tous les champs de format
  sont désactivés et l'onglet l'explique (« verrouillé pendant un match en
  cours »). Le serveur ignore de toute façon ces champs sur un match LIVE.

### Onglet Planning

- **Court** : choix parmi les courts du référentiel (ou aucun).
- **Heure prévue** : champ heure (HH:MM).
- **Statut** : Prévu / En direct / Terminé / Annulé.
  - Passer un match en « Terminé » le sort de la file et retire sa mise en
    avant ; si c'est un quart ou une demi, le vainqueur est **promu
    automatiquement** dans le tableau final.
  - « Annulé » conserve le match dans l'historique (colonne Terminés, badge).
- **Mise en avant** : interrupteur « Afficher ce match sur le scoreboard TV »
  avec le rappel : un seul match à la fois ; l'activer retire l'actuel.
  (La désactivation de la mise en avant d'un match se fait en mettant un autre
  match en avant, ou en terminant le match.)

---

## Gestion des erreurs

- Toute erreur (génération, réordonnancement, édition, mise en avant) affiche le
  message renvoyé par le serveur, dans le panneau s'il est ouvert, sinon en
  bandeau d'écran. Les erreurs de validation détaillées par champ sont montrées
  près des champs concernés.
- Après une erreur de glisser-déposer, la file est rechargée depuis le serveur
  (pas d'état visuel divergent).

## États limites

| Situation | Comportement |
|---|---|
| Aucune épreuve active | État vide avec lien vers Tournoi. |
| Aucun match | Trois colonnes vides + invite : générer les matchs de poule (ou créer le tableau final pour la phase finale). |

## Données

- Le kanban est chargé au montage et au changement d'épreuve, rechargé après
  chaque mutation. L'écran se rafraîchit périodiquement (de l'ordre de quelques
  secondes) pour refléter les scores et fins de match saisis par l'arbitre.

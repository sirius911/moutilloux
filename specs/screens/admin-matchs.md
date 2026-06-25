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

# Spec fonctionnelle — Écran Calendrier des matchs

## Rôle de l'écran

L'écran Calendrier (`/admin/events/:eventId/matches`, intitulé **« Calendrier des matchs »**)
agence les matchs de l'**épreuve active** dans le temps : il transforme la liste
des matchs de poule en un **planning ordonné par journée**, sur un court unique.

On y voit d'un coup d'œil **qui joue, quand, contre qui**. L'admin pose les
matchs (manuellement ou via la pré-pose), l'écran **estime les heures** et les
recale au fil du tournoi.

> Le modèle (états dérivés, heures estimées, repos, pré-pose, capacité) est décrit
> dans [[planning]] ; cette spec décrit l'UI et les flux.

Remplace l'ancien kanban à trois colonnes (Backlog / File d'attente / Terminés —
décision 17 de [[admin-panel-map]]).

---

## Cycle de vie

1. **Génération** (action de cet écran) : crée le round-robin → tous les matchs
   naissent **à planifier**, et verrouille la composition des poules (voir
   [[admin-poules]]). Générer les matchs **vaut** validation des poules : il n'y a
   pas d'étape « valider les poules » distincte.
2. **Pré-pose** (optionnelle) : range automatiquement la pile à planifier.
3. **Ajustement manuel** : glisser-déposer pour planifier / réordonner / insérer
   des pauses.
4. **Déroulé** : l'arbitre fait vivre les matchs (En cours → Terminé) ; les heures
   à venir se recalent.

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active, en
  lieu et place du fil d'ariane (décision 16 de [[admin-panel-map]]). Le **choix
  d'épreuve navigue** vers `/admin/events/:eventId/matches` (`router.push`) ; l'URL
  fait foi et survit au rechargement (voir [[routing-context]]).
- Titre « Calendrier des matchs », sous-titre « Qui joue, quand, contre qui ».
- Actions :
  - **« Générer les matchs de poule »** → modale de génération (prérequis : crée
    les matchs à planifier).
  - **« Pré-poser »** → range automatiquement la pile à planifier (voir flux).
    Désactivé quand la pile est vide.

### Pile « À planifier »

- Colonne latérale listant les matchs `SCHEDULED` sans position, **groupés par
  poule**.
- Chaque carte : pastille de poule, « {A} vs {B} », poignée de déplacement (⋮⋮).
- Compteur. C'est aussi une zone de dépôt : y déposer un match planifié l'y renvoie
  (= dé-planifie, perte de la journée et de la position).
- État « tout placé » : « Tout est planifié ».

### Journées

Empilées verticalement (pas d'onglets). Une section par journée de jeu (`PlayDay`) :
- En-tête : nom + date, nombre de matchs ; sous-ligne « Court central · début HH:MM
  · fin estimée ~HH:MM ».
- **Pastille de capacité** : « Cible HH:MM » (dans les temps) ou « Dépasse HH:MM »
  (surlignée) — alerte souple, jamais bloquante (voir [[planning]]).
- Action discrète **« + pause »** : insère une bande de pause dans la journée.
- Liste ordonnée des lignes (matchs + pauses) ; zone de dépôt.

### Ligne de match

- **Heure estimée** : `~HH:MM` (heure réelle, sans tilde, si terminé), en chiffres
  tabulaires.
- **Puce d'état** : Terminé / En cours / Next / Planifié (couleurs — voir légende).
- **Affiche** : pastille de poule, « {A} vs {B} ».
- **⚠ repos** si le match est adjacent, dans la séquence, à un autre match du même
  joueur (voir [[planning]]).
- Poignée de déplacement (⋮⋮) sur les lignes déplaçables (hors match en cours).
- Cliquer la ligne ouvre le **panneau d'édition** du match.

### Bande de pause

- Ligne pleine largeur « {libellé} · {durée} min · ~HH:MM », déplaçable et
  retirable. Le moteur d'ETA l'enjambe (l'aval se décale d'autant).

### Légende

- Rappel des puces d'état (Terminé, En cours, Next, Planifié) et du marqueur
  ⚠ repos insuffisant.

---

## Modale « Générer les matchs de poule »

- Sous-titre : « Round-robin complet pour chaque poule. »
- Tableau de répartition : pour chaque poule — lettre, nombre de joueurs, nombre de
  matchs à créer (n·(n−1)/2) ; ligne Total.
- Le format appliqué est le **format de poule par défaut** (1 set à 5 jeux,
  tie-break à 4-4) ; la modale l'indique en clair. Il reste ajustable ensuite match
  par match via le panneau d'édition.
- Bouton de confirmation : « Générer N matchs ».
- Génération **idempotente** : les rencontres déjà créées ne sont pas dupliquées ;
  relancer ne crée que les paires manquantes. La réponse indique le nombre
  réellement créé.
- Cas limites : aucune poule, ou poules à moins de 2 participants → 0 match à créer,
  confirmation désactivée.
- Après génération, les nouveaux matchs apparaissent dans la **pile « À planifier »**
  et la composition des poules devient verrouillée (voir [[admin-poules]]).

---

## Flux : planifier / réordonner (glisser-déposer)

1. L'admin glisse une carte de la pile vers une journée (à la position voulue), ou
   réordonne une ligne dans une journée / entre journées, ou renvoie une ligne vers
   la pile.
2. La **séquence complète** est envoyée au serveur ; les positions `order_index`
   sont (ré)attribuées (`POST …/matches/reorder/`). Un match renvoyé à la pile perd
   sa position et sa journée.
3. Un match entrant en journée reçoit le **court unique** s'il n'en a pas
   (mono-court).
4. Le match **en cours** garde sa place dans la séquence (non déplaçable).
5. Les heures estimées et le « Next » sont recalculés après chaque changement.

## Flux : pré-poser

1. L'admin clique « Pré-poser ».
2. La pile est rangée automatiquement — **entrelacée par poule**, repos respecté,
   **distribuée sur les journées** selon leur capacité — **sans toucher** aux matchs
   déjà placés (voir [[planning]]). L'alerte de capacité d'une journée peut
   s'allumer si la pré-pose la fait déborder.

## Flux : insérer / déplacer une pause

1. « + pause » sur une journée ajoute une bande (libellé, durée) en fin de séquence.
2. La pause se déplace comme une ligne ; le moteur d'ETA l'enjambe.

## Flux : mettre un match en avant

1. L'admin met un match « à l'antenne » (depuis le panneau d'édition, ou une action
   dédiée sur la ligne).
2. Une **confirmation** explicite l'effet : « Ce match passe EN DIRECT et devient le
   match affiché sur la TV. Le match actuellement à l'antenne est retiré. »
3. À la confirmation : le match devient `LIVE`, prend le badge « EN AVANT » ;
   l'éventuel match précédemment en avant perd son statut de diffusion.

---

## Panneau d'édition de match (volet latéral)

Ouvert au clic sur une ligne. En-tête : étape, « {A} vs {B} », badges d'état
(PRÉVU / EN DIRECT / TERMINÉ / ANNULÉ), heure estimée, « ★ MIS EN AVANT ». Trois
onglets : **Score**, **Format**, **Planning**. Pied : « Annuler » et
« Enregistrer » (désactivé pendant la sauvegarde ; les erreurs s'affichent dans le
pied sans fermer le panneau).

### Onglet Score

- Mention : « éditable en cas d'erreur arbitre » — la saisie normale du score se
  fait sur l'écran Arbitre ; cet onglet sert aux **corrections**.
- Grille par joueur : sets gagnés, jeux du set en cours, points du jeu en cours.
- Interrupteur « Tie-break activé » (quand désactivé, les points de tie-break sont
  remis à zéro).
- Sélecteur **Vainqueur** : « À déterminer » / {A} / {B}.
- Les valeurs saisies sont enregistrées telles quelles (pas de recalcul auto) ; les
  valeurs négatives sont ramenées à zéro.

### Onglet Format

- Préréglage de format (« Poule : 1 set à 5, TB à 4-4 », « Quart », « Demi »,
  « Finale », « Manuel ») et règles détaillées (jeux pour gagner le set, seuil de
  tie-break, sets gagnants, points de tie-break, écart de 2 points, mode du set
  décisif, points du super tie-break) ; service initial : {A} / {B}.
- **Verrouillage** : quand le match est EN DIRECT, tous les champs de format sont
  désactivés et l'onglet l'explique (« verrouillé pendant un match en cours »). Le
  serveur ignore de toute façon ces champs sur un match `LIVE`.

### Onglet Planning

- **Journée** : la journée de jeu à laquelle le match est affecté (ou « à
  planifier »). Changer la journée déplace le match dans le calendrier.
- **Heure estimée** : **lecture seule** — dérivée de l'ordre et des durées (voir
  [[planning]]). Il n'y a **pas** de saisie d'heure manuelle (décision 18 de
  [[admin-panel-map]]).
- **Court** : mono-court — information seulement (« Central »), non éditable
  (décision 12 / 19).
- **Statut** : Prévu / En direct / Terminé / Annulé.
  - Passer en « Terminé » sort le match de la séquence et retire sa mise en avant ;
    si c'est un quart ou une demi, le vainqueur est **promu automatiquement** dans
    le tableau final (voir [[admin-tableau-final]]).
  - « Annulé » conserve le match dans l'historique (badge ANNULÉ, hors séquence).
- **Mise en avant** : interrupteur « Afficher ce match sur le scoreboard TV »
  (un seul match à la fois ; l'activer retire l'actuel).
- La **position** dans la séquence se règle par glisser-déposer, pas dans ce
  panneau.

---

## Gestion des erreurs

- Toute erreur (génération, réordonnancement, pré-pose, édition, pause, mise en
  avant) affiche le **message renvoyé par le serveur**, dans le panneau s'il est
  ouvert, sinon en bandeau d'écran. Les erreurs de validation par champ sont
  montrées près des champs concernés.
- Après une erreur de glisser-déposer, le calendrier est **rechargé** depuis le
  serveur (pas d'état visuel divergent).

## États limites

| Situation | Comportement |
|---|---|
| Aucune épreuve active | État vide avec lien vers Tournoi. |
| Aucun match | Pile et journées vides + invite : générer les matchs de poule. |
| Aucune journée configurée | Invite à définir au moins une journée de jeu (date, début, fin cible — voir [[planning]]). Sans journée, on ne peut que générer / garder les matchs « à planifier ». |
| Pile non vide en fin de planification | Ce n'est pas une erreur : les matchs restants demeurent « à planifier ». |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/matches`) : l'URL fait foi, le store la reflète, et un
  `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve. Le calendrier lui-même couvre
  toute l'**édition** (dérivée de l'épreuve) ; le `:eventId` cible les actions par
  épreuve (générer, pré-poser) et la mise en évidence.
- Le calendrier est chargé au montage et au changement d'épreuve, rechargé après
  chaque mutation. L'écran se rafraîchit **périodiquement** (de l'ordre de quelques
  secondes ; cible ~2 s, voir [[planning]]) pour refléter les passages En cours /
  Terminé saisis par l'arbitre et **recaler les heures estimées**.

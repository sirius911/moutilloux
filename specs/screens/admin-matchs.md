---
type: screen
module: admin/matchs
fichiers:
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/components/modals/PlayDayModal.vue
  - frontend/app/src/stores/event.ts
  - live/api_views.py
  - live/admin_views.py
  - live/models.py
---

# Spec fonctionnelle — Écran Calendrier des matchs

## Rôle de l'écran

L'écran Calendrier (`/admin/events/:eventId/matches`, intitulé **« Calendrier des matchs »**)
agence les matchs de l'**épreuve active** dans le temps : il transforme la liste
des matchs — **poules et tableau final** — en un **planning ordonné par
journée**, sur un court unique.

On y voit d'un coup d'œil **qui joue, quand, contre qui**. L'admin pose les
matchs (manuellement ou via la pré-pose), l'écran **estime les heures** et les
recale au fil du tournoi.

> Le modèle (états dérivés, heures estimées, repos, pré-pose, capacité) est décrit
> dans [[planning]] ; cette spec décrit l'UI et les flux.

Remplace l'ancien kanban à trois colonnes (Backlog / File d'attente / Terminés —
décision 17 de [[admin-panel-map]]).

---

## Cycle de vie

Les matchs **existent déjà** quand on arrive ici : ils sont créés par
**« Débuter l'épreuve »** (écran Tournoi, voir [[cycle-de-vie-epreuve]]), qui
fait naître **à planifier** les matchs de poule **et** le squelette du tableau
final (QF/SF/F/P3, étiquetés « A1 vs D2 » tant que non résolus — voir
[[planning]], « Matchs de tableau au calendrier »), et verrouille la composition
des poules. Le calendrier n'est donc disponible que pour une épreuve
**`EN_COURS`**.

1. **Pré-pose** (optionnelle) : range automatiquement la pile à planifier.
2. **Ajustement manuel** : glisser-déposer pour planifier / réordonner / insérer
   des pauses.
3. **Déroulé** : l'arbitre fait vivre les matchs (En cours → Terminé). Un match
   joué **reste à sa place** dans la journée, verrouillé (voir « Ligne de match ») ;
   les heures à venir se recalent sur son heure réelle.
4. **Ajustements ponctuels** : un **ajout tardif** (voir [[cycle-de-vie-epreuve]])
   fait réapparaître de nouveaux matchs dans la pile « à planifier ».

---

## Éléments d'interface

### En-tête de page

- **Sélecteur d'épreuve** : liste déroulante des épreuves de l'édition active, en
  lieu et place du fil d'ariane (décision 16 de [[admin-panel-map]]). Le **choix
  d'épreuve navigue** vers `/admin/events/:eventId/matches` (`router.push`) ; l'URL
  fait foi et survit au rechargement (voir [[routing-context]]).
- Titre « Calendrier des matchs », sous-titre « Qui joue, quand, contre qui ».
- Actions :
  - **« Gérer les journées »** → ouvre la modale de gestion des journées de jeu
    (`PlayDay`) : créer, modifier, supprimer une journée (voir « Modale Gérer les
    journées » ci-dessous). C'est le point d'entrée **dans l'application** pour
    configurer le calendrier (plus de passage obligé par l'admin Django).
  - **« Pré-poser »** → range automatiquement la pile à planifier (voir flux).
    Désactivé quand la pile est vide.

### Pile « À planifier »

- Colonne latérale listant les matchs `SCHEDULED` sans position de **toute
  l'édition** (le calendrier est édition-scoped, voir Données), **tous stages
  confondus**, **groupés par épreuve puis par poule** — les matchs de tableau
  d'une épreuve forment un groupe « Tableau » (ordre QF → SF → F/P3). Les
  matchs des autres épreuves sont **atténués** (mise en évidence de l'épreuve
  active) mais restent déplaçables.
- Chaque carte : pastille de poule (ou pastille d'étape « QF1 », « SF2 »…),
  « {A} vs {B} » — les slots non résolus affichent leur **étiquette de
  provenance** (« A1 vs D2 », « Vainqueur QF1 ») —, poignée de déplacement (⋮⋮).
- Compteur. C'est aussi une zone de dépôt : y déposer un match planifié l'y renvoie
  (= dé-planifie, perte de la journée et de la position).
- État « tout placé » : « Tout est planifié ».

### Colonne « Annulés »

- Colonne latérale distincte, **affichée seulement s'il existe au moins un match
  annulé** (sinon masquée). Liste les matchs `CANCELED` (annulation sèche, sans
  vainqueur), retirés de leur journée. Couvre **toute l'édition**, groupée par
  épreuve puis poule, matchs des autres épreuves atténués.
- Chaque carte : pastille de poule, « {A} vs {B} », badge **ANNULÉ**.
- **Lecture seule** : un match annulé ne se glisse pas. Pour le réactiver, passer
  par le panneau d'édition (onglet Planning → Statut).
- L'annulation **retire le match de la séquence** : le créneau libéré est récupéré
  et les heures de la journée se recalent (voir [[planning]]).

### Journées

Empilées verticalement (pas d'onglets), dans la **zone scrollable** de l'écran.
Une section par journée de jeu (`PlayDay`), **repliable / dépliable** au clic
sur son en-tête (chevron d'état) :

- **État par défaut au chargement** : les journées **entièrement jouées**
  (plus aucun match `SCHEDULED` ni `LIVE` dans leur séquence) arrivent
  **repliées** ; la journée courante et les journées à venir arrivent
  **dépliées**. L'état plié/déplié n'est pas persisté : la règle est
  réappliquée à chaque chargement de la page (le repli manuel vaut pour la
  session d'écran en cours).
- **Repliée**, la carte se réduit à son en-tête, qui porte un **résumé
  riche** : nom + date, **compteur de matchs** (joués / total), **plage
  horaire** (« début HH:MM → fin estimée ~HH:MM », heure de fin réelle sans
  tilde si la journée est finie) et la **pastille de capacité** — l'alerte
  « Dépasse HH:MM » reste donc visible sans déplier.
- **Dépliée**, la carte **ne clippe pas son contenu** — pas d'`overflow:
  hidden` sur la carte (`.play-day`) : il casse le défilement et tout
  positionnement `sticky` interne (l'arrondi des coins est porté par l'en-tête
  et le pied de carte, pas par un clip).
- En-tête (déplié) : nom + date, nombre de matchs ; sous-ligne « Court central ·
  début HH:MM · fin estimée ~HH:MM ». L'**heure de début est éditable en place** :
  cliquer « début HH:MM » ouvre un sélecteur d'heure inline (même mutation que
  « Modifier » dans la modale Gérer les journées) — c'est le moyen rapide de
  décaler le premier match de la journée, les heures restant dérivées
  (décision 18, [[planning]]).
- **Pastille de capacité** : « Cible HH:MM » (dans les temps) ou « Dépasse HH:MM »
  (surlignée) — alerte souple, jamais bloquante (voir [[planning]]).
- Action discrète **« + pause »** : insère une bande de pause dans la journée.
- Liste ordonnée des lignes (matchs + pauses) ; zone de dépôt.
- Les journées affichent **tous les matchs de l'édition** (mono-court : une seule
  séquence, toutes épreuves confondues). Les lignes des autres épreuves sont
  **atténuées** ; quand plusieurs épreuves cohabitent, chaque ligne porte le nom
  de son épreuve — **pastille compacte**, dimensionnée à son contenu, jamais
  étirée sur l'espace restant de la ligne (retours 2026-07-12).

### Ligne de match

- **Heure estimée** : `~HH:MM` (heure réelle, sans tilde, si terminé), en chiffres
  tabulaires.
- **Puce d'état** : Terminé / En cours / Next / Planifié (couleurs — voir légende).
- **Teinte de ponctualité** sur la ligne (dérivée, tolérance 5 min — règles dans
  [[planning]]) : **rouge** = en retard et pas démarré, **orange** = démarré en
  retard ou qui s'éternise, **vert** = en cours et à l'heure. Les lignes dans
  les temps, terminées ou annulées ne portent aucune teinte.
- **Affiche** : pastille de poule (ou d'étape pour un match de tableau),
  « {A} vs {B} » — noms selon [[affichage-participant]] (`displayName`, donc
  nom d'équipe en Double) ; étiquettes de provenance si les slots ne sont pas
  résolus, « À désigner » en dernier recours (jamais « TBD »).
- **⚠ repos** si le match est adjacent, dans la séquence, à un autre match du même
  joueur (voir [[planning]]) — inévaluable sur des slots non résolus (best-effort,
  réévalué à la résolution).
- Poignée de déplacement (⋮⋮) sur les seules lignes **déplaçables** (`SCHEDULED`).
  Les matchs **en cours et terminés** sont **verrouillés à leur place** (visibles,
  non déplaçables).
- Cliquer la ligne ouvre le **panneau d'édition** du match.

### Bande de pause

- Ligne pleine largeur « {libellé} · {durée} min · ~HH:MM », déplaçable et
  retirable. Le moteur d'ETA l'enjambe (l'aval se décale d'autant).

### Légende

- Rappel des puces d'état (Terminé, En cours, Next, Planifié), des **teintes de
  ponctualité** (rouge / orange / vert) et du marqueur ⚠ repos insuffisant.

---

## Aperçu du round-robin (au moment de « Débuter »)

La génération du round-robin **n'est plus une action de cet écran** : elle est
déclenchée par **« Débuter l'épreuve »** (écran Tournoi, voir
[[cycle-de-vie-epreuve]]). La confirmation de « Débuter » affiche l'aperçu —
répartition par poule (lettre, nombre de joueurs, n·(n−1)/2 matchs, total) et le
**format de poule par défaut** (1 set à 5, TB à 4-4, ajustable ensuite match par
match via le panneau d'édition).

La génération est **idempotente et additive** : les rencontres déjà créées ne sont
pas dupliquées ; un **ajout tardif** ne crée que les paires manquantes du nouveau
venu. Les matchs créés arrivent dans la **pile « À planifier »**.

---

## Flux : planifier / réordonner (glisser-déposer)

1. L'admin glisse une carte de la pile vers une journée (à la position voulue), ou
   réordonne une ligne dans une journée / entre journées, ou renvoie une ligne vers
   la pile.
   - Une journée **repliée** n'est pas une zone de dépôt : pendant un drag,
     **survoler son en-tête ~600 ms la déplie** (elle reste dépliée après le
     drop), ce qui permet de poser la carte à la position exacte voulue. Pas de
     dépôt direct sur l'en-tête replié.
2. La **séquence complète** est envoyée au serveur ; les positions `order_index`
   sont (ré)attribuées (`POST …/matches/reorder/`). Un match renvoyé à la pile perd
   sa position et sa journée.
3. Un match entrant en journée reçoit le **court unique** s'il n'en a pas
   (mono-court).
4. Les matchs **en cours et terminés** gardent leur place dans la séquence
   (verrouillés, non déplaçables) ; seuls les matchs `SCHEDULED` se glissent.
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

## Modale « Gérer les journées »

Ouverte par **« Gérer les journées »**. Gère les journées de jeu (`PlayDay`) de
l'**édition** courante — le calendrier étant édition-scoped (voir [[planning]] et
[[routing-context]]).

- **Liste** des journées existantes, triées par date : pour chacune, **date**,
  **heure de début**, **heure de fin cible**, nombre de matchs/pauses rattachés,
  et actions **Modifier** / **Supprimer**.
- **« Générer depuis l'édition »** : propose une journée par jour entre les
  **dates de début et de fin de l'édition** (bornes incluses), en sautant les
  dates ayant déjà une journée. Un mini-formulaire fixe la plage horaire commune
  avant validation — défaut **9:00 → 20:00** — et affiche l'aperçu des journées
  qui seront créées (pas de création silencieuse). Chaque journée reste ensuite
  modifiable individuellement. Action désactivée (avec explication) si
  l'édition n'a pas ses dates, ou si tous les jours sont déjà couverts.
  Contrat : [[planning]] (`play-days/generate/`).
- **« + Nouvelle journée »** : formulaire — **date** (requise), **heure de début**
  (requise), **heure de fin cible** (requise). À l'enregistrement, la journée
  apparaît immédiatement dans le calendrier (section vide prête à recevoir des
  matchs).
- **Modifier** : édite date / début / fin cible. Les heures estimées des matchs de
  la journée sont recalculées (voir [[planning]]).
- **Supprimer** : **refusée par le serveur** si la journée porte encore des pauses,
  ou des matchs `SCHEDULED`/`LIVE` — le message est affiché et invite à renvoyer
  d'abord ses matchs vers la pile « à planifier » (**actionnable**, on peut
  réessayer ensuite). Si la journée porte au moins un match `FINISHED`, le refus
  est **définitif** : la journée est conservée comme **archive** et le message
  l'indique explicitement. Dans ce cas, le bouton **Supprimer** est **désactivé**
  côté UI (`PlayDayModal.vue`) dès qu'un match de la journée a le statut
  `FINISHED`. Une journée **vide** se supprime après une confirmation simple.
- Les heures ne sont jamais saisies sur les matchs (décision 18) ; cette modale ne
  règle que les **bornes de journée**, l'ETA reste dérivée.
- Erreurs serveur affichées dans la modale, saisie conservée.

> Contrat : `CRUD PlayDay` (voir [[planning]]). Conventions back (CLAUDE.md §5) :
> chaque mutation est d'abord une **fonction de service** réutilisable dans
> `admin_views.py`, exposée par un endpoint `/api/` fin ; `live/urls.py` est câblé
> par l'orchestrateur.

## Panneau d'édition de match (volet latéral)

Ouvert au clic sur une ligne. En-tête : étape, « {A} vs {B} », badges d'état
(PRÉVU / EN DIRECT / TERMINÉ / ANNULÉ), heure estimée, « ★ MIS EN AVANT ». Quatre
onglets : **Score**, **Format**, **Planning**, **Affiche**. Pied : « Annuler » et
« Enregistrer » (désactivé pendant la sauvegarde ; les erreurs s'affichent dans le
pied sans fermer le panneau). Un raccourci **« Affiche »** sur la ligne du
calendrier ouvre le panneau directement sur cet onglet.

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
  - Passer en « Terminé » **verrouille le match à sa place** (il reste visible dans
    sa journée, avec son heure réelle) et retire sa mise en avant ; si c'est un
    quart ou une demi, le vainqueur est **promu automatiquement** dans le tableau
    final (voir [[admin-tableau-final]]). Le match **ne quitte pas** la séquence.
  - « Annulé » (`CANCELED`) = annulation sèche, **sans vainqueur** : le match
    **quitte sa journée** (perd sa place) et bascule dans la **colonne « Annulés »**
    (voir ci-dessus). Conservé dans l'historique, badge ANNULÉ.
  - Un **forfait / walkover** est distinct de l'annulation : match « Terminé »
    **avec vainqueur** par défaut, issu de l'abandon d'un inscrit — il **reste à sa
    place** (verrouillé, libellé « Forfait »). Mécanique dans [[cycle-de-vie-epreuve]].
- **Mise en avant** : interrupteur « Afficher ce match sur le scoreboard TV »
  (un seul match à la fois ; l'activer retire l'actuel).
- La **position** dans la séquence se règle par glisser-déposer, pas dans ce
  panneau.

### Onglet Affiche

Génération et choix de l'**affiche IA** du match (mécanique complète :
[[affiche-match]]) :

- **Affiche retenue** : aperçu de `Match.poster` si elle existe, avec action
  **Retirer** (confirmation simple).
- **Formulaire de génération** : un champ « attitude » par joueur, pré-rempli
  par **tirage au sort** parmi les attitudes de la fiche (`Player.attitudes`),
  remplaçable par un choix explicite avant de lancer (voir [[affiche-match]]). Bouton
  **« Générer 2 propositions »** — désactivé (avec explication) si un joueur
  n'a pas de photo, si les deux sides ne sont pas résolus, ou si une
  génération est déjà en cours.
- **Suivi** : pendant la génération (asynchrone, ~1-2 min), l'onglet affiche la
  progression par polling ; on peut fermer le panneau et revenir.
- **Galerie de choix** : les 2 candidates du lot côte à côte ; **Choisir**
  promeut l'élue en affiche du match et purge le lot ; **Relancer** remplace le
  lot (les non-retenues ne sont jamais conservées).
- Erreurs (clé API absente, refus de modération, échec réseau) : message
  serveur affiché dans l'onglet, jamais d'échec silencieux.

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
| Épreuve pas encore débutée (`INSCRIPTION`) | Le calendrier n'est pas disponible : invite à **débuter l'épreuve** depuis l'écran Tournoi (voir [[cycle-de-vie-epreuve]]). |
| Aucune journée configurée | État vide invitant à **créer les journées** via **« Gérer les journées »** — en un geste avec « Générer depuis l'édition » si l'édition a ses dates, sinon journée par journée (voir Modale ci-dessous et [[planning]]). Sans journée, on ne peut que générer / garder les matchs « à planifier ». Ne renvoie **pas** vers l'admin Django. |
| Pile non vide en fin de planification | Ce n'est pas une erreur : les matchs restants demeurent « à planifier ». |

## Données

- L'**épreuve active** vient du segment d'URL `:eventId`
  (`/admin/events/:eventId/matches`) : l'URL fait foi, le store la reflète, et un
  `:eventId` absent ou périmé est rattrapé par la garde de route (voir
  [[routing-context]]). Recharger conserve l'épreuve. Le calendrier lui-même couvre
  toute l'**édition** (dérivée de l'épreuve) ; le `:eventId` cible les actions par
  épreuve (générer, pré-poser) et la **mise en évidence** (les matchs des autres
  épreuves sont affichés atténués, jamais masqués : filtrer la séquence avant de
  la renvoyer au serveur dé-planifierait les matchs absents — contrat de
  réordonnancement dans [[planning]]).
- Le calendrier est chargé au montage et au changement d'épreuve, rechargé après
  chaque mutation. L'écran se rafraîchit **périodiquement** (de l'ordre de quelques
  secondes ; cible ~2 s, voir [[planning]]) pour refléter les passages En cours /
  Terminé saisis par l'arbitre et **recaler les heures estimées**.

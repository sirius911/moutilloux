---
type: screen
module: tv/live
fichiers:
  - frontend/app/src/views/tv/TvLayout.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/stores/live.ts
  - frontend/app/src/composables/usePolling.ts
  - frontend/app/src/composables/useScale.ts
  - live/api_views.py
---

# Spec fonctionnelle — TV live (scoreboard ⇄ carousel)

## Rôle de l'écran

`/tv/live` est **l'unique affichage public** du tournoi (une TV, un court —
voir [[tv-map]]). Il est en lecture seule, sans aucune interaction attendue, et
bascule **automatiquement** entre quatre états :

- **ÉCHAUFFEMENT** quand le match `LIVE` n'est pas encore lancé
  (`playStartedAt` nul, voir [[cycle-de-vie-match]]) : l'affiche du match en
  grand + compte à rebours ;
- **SCOREBOARD** dès que le match est lancé : le score en grand + l'enjeu du
  match + la carte « À préparer » ;
- **FIN DE MATCH** (~30 s) quand le match affiché vient de se terminer : le
  vainqueur et le score final ;
- **CAROUSEL** sinon : rotation de slides d'information (stats, résultats,
  poules, tableau, programme, annonces).

La bascule est **dérivée** de l'état serveur (`hero` et sa phase, voir
[[tv-state]] ; la fenêtre Fin de match est tenue côté front) — jamais d'action
manuelle. La scène est fixée à 1920×1080 et mise à l'échelle sur l'écran réel
(`TvLayout` / `useScale`).

---

## État SCOREBOARD (un match est en jeu)

Scène **composée** : le score en **bande basse** (l'élément dominant de
l'écran), la carte « À préparer » à droite, l'enjeu au-dessus de la bande
(panneau de poule à gauche, ou phase de tableau en grand), l'affiche en fond.
Référence design : la variante **« editorial »** du mock
(`frontend/design/scoreboard.jsx`, `ScoreboardEditorial`) pour la matière
typographique (chiffres géants, hiérarchie), et le **`PrepPanel`** du même mock
pour la carte de droite — mais la **structure en deux lignes** de la bande de
score, décrite ci-dessous, prime sur le mock (retours 2026-07-10).

### Bandeau haut (fin)

- Marque du tournoi (« OPEN DE MOUTILLOUX · ÉDITION {année} »), intitulé de
  l'étape (`stageLabel`), pastille « EN DIRECT », badge « JEU DÉCISIF » si
  tie-break en cours.

### Bande basse : le score broadcast (l'élément dominant)

Bloc unique ancré en bas de scène, **deux lignes, une par joueur** — comme les
bandeaux des retransmissions TV : **chaque donnée vit sur la ligne de son
joueur**, l'association joueur ↔ score est **structurelle**. Aucun chiffre
« flottant » rattaché par une convention de position (retours 2026-07-10 :
les jeux géants centrés, détachés des noms, étaient inattribuables).

- Chaque ligne, de gauche à droite : balle de service côté serveur, nom
  (nom d'équipe en Double), tête de série, puis les colonnes de score alignées
  à droite : **sets gagnés**, **jeux du set en cours en très grand**
  (l'élément dominant de la scène), **points du jeu en cours**.
- Les colonnes sont surmontées d'en-têtes explicites — **« SETS »,
  « JEUX · SET {n} », « POINTS »** : l'étiquette lève l'ambiguïté points/jeux
  pour un spectateur qui arrive en cours de match, l'alignement en colonnes
  lève l'ambiguïté joueur/score.
- Les points affichent **`displayPointA/B`** de `_pack_match`
  (`0/15/30/40/AV`, égalité `40/40`, points bruts en tie-break) — le front ne
  recalcule **jamais** le libellé depuis les points bruts.
- **Signal broadcast sur l'avantage** : le « AV » du côté avantagé passe en
  **accent**, le « 40 » d'en face reste blanc — l'œil voit qui a la balle de
  jeu.
- **L'accent est réservé aux signaux porteurs de sens** (balle de service,
  « AV », badge « JEU DÉCISIF ») — jamais décoratif : pas de couleur d'accent
  systématique sur un côté, un chiffre coloré d'un seul côté suggère un sens
  (serveur ? meneur ?) qu'il n'a pas (retours 2026-07-10).

### Pied discret

- Court, durée du match (`clock`), horloge (`now`).

### Fond de scène : l'affiche du match

Si le match a une **affiche générée** (`hero.posterUrl`, voir
[[affiche-match]]), elle remplace le fond de court sur toute la scène — la
bande de score se compose par-dessus. Sans affiche, le fond de court
demeure.

### L'enjeu du match (au-dessus de la bande de score)

L'**enjeu du match** (décision 4 de [[tv-map]], amendée par la décision 13)
dépend de la phase du hero :

- **Match de poule** → le **classement de la poule** des deux joueurs, en
  panneau semi-transparent d'environ **480 px**, ancré à gauche, contraste
  adouci (standings : rang, nom, V/D, points, badge Q — affiché seulement si
  la poule est **terminée**, voir [[cycle-de-vie-epreuve]]), les deux joueurs
  du match mis en évidence. Le public voit ce que le match peut changer.
  Données fournies par [[tv-state]] (`stake`) ; si l'enjeu n'est pas
  disponible, le panneau est masqué — jamais d'erreur visible.
- **Match de tableau** (QF/SF/F/P3) → **pas de panneau** : la **phase du
  match en grand** (`stageLabel` : « Quart de finale », « Demi-finale »,
  « Finale », « 3e place »), centrée au-dessus de la bande de score. Le
  mini-tableau est **retiré** (retours 2026-07-10 : tronqué par sa hauteur
  bornée, illisible à distance de TV, et il recouvrait le nom d'un joueur) —
  le tableau complet reste visible en slide du carousel entre les matchs.
- **Contrainte de composition** : panneau de poule et libellé de phase vivent
  entièrement dans la **zone libre au-dessus de la bande de score** — ils ne
  recouvrent jamais les lignes joueurs ni la carte « À préparer ».

### Droite : la carte « À préparer » (PrepPanel)

Carte **flottante en haut à droite** (~360 px, portée du `PrepPanel` du mock),
**uniquement s'il existe un next** (défini par [[tv-state]]) :

- avatars/initiales des deux joueurs, « {A} vs {B} », étiquette de poule/étape,
  heure estimée (`~HH:MM`), et l'appel « Présentez-vous au juge-arbitre ».
- But : laisser les joueurs suivants se préparer pendant le match en cours.
- Remplace l'ancien bandeau pleine largeur au-dessus de la bande de score
  (portage dégradé du design, retiré).

---

## État ÉCHAUFFEMENT (match démarré, pas encore lancé)

Actif quand le `hero` est `LIVE` avec `playStartedAt` nul (l'arbitre a démarré
le match, le serveur n'est pas encore choisi — voir [[cycle-de-vie-match]]) :

- **L'affiche du match en plein écran** (sans bande de score) — c'est le moment
  de mise en avant du dispositif [[affiche-match]]. Sans affiche : **fond de
  court seul**, le bloc central porte toute la scène. Il n'y a **pas** de
  composition typographique des noms en très grand : elle entrait en collision
  avec le compte à rebours central (retours 2026-07-09).
- **Bloc central unique** : libellé **« ÉCHAUFFEMENT »** + **compte à rebours**
  (5 min, constante), dérivé de `warmupStartedAt` — même source que la tablette
  arbitre, donc synchronisé. À 0:00, le compte à rebours laisse place à un
  libellé d'imminence (« Le match va commencer ») — rien d'automatique.
- Sous le compte à rebours : joueurs (« {A} vs {B} »), étape, court.
- La carte « À préparer » reste affichée s'il existe un next.
- La scène bascule sur le SCOREBOARD au poll où `playStartedAt` se remplit.

---

## État FIN DE MATCH (~30 s, tenu côté front)

Quand le `hero` disparaît du poll alors que la TV affichait un match :

1. Le front fait un **fetch one-shot** de `GET /api/matches/:id/` (lecture
   publique) pour récupérer l'**état final** — le dernier état pollé ne
   contient pas le point gagnant, puisque le serveur ne renvoie plus le match
   une fois `FINISHED`.
2. Si le match est `FINISHED` avec un vainqueur → scène **« photo finish »**
   pendant **~30 s** : l'affiche du match en fond plein écran, « VICTOIRE »,
   le **nom du vainqueur en très grand**, le **score par sets** (`setScores`),
   la durée du match. Si `endReason = RETIREMENT`, la mention « Abandon »
   accompagne le score (figé en l'état).
3. Après ~30 s, fondu vers le CAROUSEL.

Règles :

- **Préemption** : un nouveau `hero` (match suivant démarré) interrompt la
  fenêtre immédiatement — le direct gagne toujours.
- Un match **rouvert** par l'admin pendant la fenêtre redevient `hero` au poll
  suivant (même préemption).
- Un match sorti du direct **sans vainqueur** (annulé, reset, mis en pause par
  un autre démarrage) ne déclenche **pas** la scène : carousel direct.
- Un **walkover** ne déclenche rien (le match n'a jamais été à l'antenne).
- La fenêtre étant tenue côté front, un **rechargement de la TV** pendant les
  30 s repart sur le carousel — assumé (choix : pas d'état serveur pour un
  écran éphémère).

---

## État CAROUSEL (aucun match LIVE)

### Cadre

- En-tête : marque + horloge (`now`).
- Pied : barre « PROCHAIN MATCH » (~heure, joueurs, à partir du *next* — masquée
  s'il n'y a pas de next, remplacée par « Programme du tournoi en cours de
  préparation ») + pastilles de pagination des slides.
- **Emprise des slides** : l'en-tête et le pied sont conservés tels quels, mais
  le corps des slides exploite la largeur de la scène 1920×1080 au plus près —
  plafond ~1760 px utiles, marges latérales réduites (retours 2026-07-09 :
  « l'espace du carrousel légèrement agrandi »).
- Rotation automatique : **~8 s par slide**, fondu. Une slide **sans contenu
  est sautée** (décision 5). Les pastilles reflètent les slides réellement
  affichables.
- **Pastille de progression** : la pastille de la slide courante se **remplit
  progressivement** sur la durée de la slide — le public voit le temps restant
  avant la suivante. Elle repart de zéro à chaque changement de slide.
- **Rotation stable** : un rafraîchissement des données (poll `tv/idle`) ne
  réinitialise **jamais** la rotation et ne change **jamais** la slide affichée
  en cours de lecture. Un changement de composition (slide devenant vide ou
  redevenant affichable) prend effet au **prochain** tick de rotation — la
  slide courante est identifiée par sa **nature** (et son épreuve pour
  Poules/Tableau), pas par sa position dans la liste.

### Slides (dans cet ordre)

| Slide | Contenu | Vide ⇒ sautée si |
|---|---|---|
| **Tournoi** | Stats agrégées de l'édition : matchs joués / total, inscrits, épreuves — et le statut (« EN ATTENTE DU PROCHAIN MATCH »). | jamais (slide par défaut) |
| **Derniers résultats** | Les **5 derniers matchs terminés** de l'édition (ordre `finished_at` décroissant — pas l'ordre calendaire), toutes épreuves : étape, joueurs (vainqueur en évidence), score par sets. | aucun match terminé |
| **Poules** | Les poules d'**une épreuve** (lettre, standings V/D/Pts, badge Q — seulement sur poule **terminée**, [[cycle-de-vie-epreuve]]) — **rotation par épreuve** : au passage suivant de la slide, l'épreuve suivante qui a des poules (décision 6). L'épreuve est nommée dans le titre. | aucune poule composée |
| **Tableau** | Le tableau final d'**une épreuve** (QF→SF→F, + 3e place si l'épreuve l'active), étiquettes de provenance sur les places vides — même rotation par épreuve. **Score par sets sur chaque ligne joueur** (chiffres alignés à droite) pour les matchs **terminés** (`setScores`) **et en direct** (sets acquis + jeux du set en cours, rafraîchis au poll) — même présentation que l'écran admin ([[admin-tableau-final]]). | aucun tableau créé |
| **Programme** | Les **N prochains matchs planifiés** (N ≈ 4–6) à partir du *next*, dans l'ordre de la séquence : ~heure, joueurs, étiquette de poule ; le premier marqué « bientôt ». Pied : « Horaires estimés — susceptibles de bouger ». **Journée courante épuisée** → titre « Programme de demain » et matchs de la journée suivante ; plus aucune journée → « Programme terminé » (slide affichée une fois puis sautée). | aucun match planifié restant |
| **Annonces** | Les annonces **actives** de l'édition (voir [[tv-state]], modèle `Announcement`), en texte grand format. | aucune annonce active |
| **Affiche** | L'**affiche du prochain match** (`posterUrl` du next, voir [[affiche-match]]) en grand, avec ~heure et joueurs — effet « à l'affiche ». | le next n'a pas d'affiche |

Toutes les heures publiques sont **approximatives** (préfixe `~`, décision 18
d'[[admin-panel-map]] / [[planning]]).

---

## Bascule d'état

1. Le front polle l'état TV (~2 s, voir Données). `hero` non nul et
   `playStartedAt` nul → ÉCHAUFFEMENT ; `hero` non nul et lancé → SCOREBOARD ;
   `hero` passant à nul depuis un match affiché → FIN DE MATCH (~30 s, fetch
   one-shot) ; sinon → CAROUSEL.
2. Les bascules sont immédiates (au poll suivant), sans transition bloquante ;
   le carousel reprend sa rotation là où il s'était arrêté.
3. Un match mis « à l'antenne » depuis l'admin ([[admin-matchs]], mise en
   avant) devient le `hero` : même mécanique, aucune logique TV spécifique
   (jamais lancé → il apparaît en échauffement ; repris → directement le
   scoreboard, voir [[cycle-de-vie-match]]).

## Gestion des erreurs

- Échec d'un poll : la TV **conserve le dernier état affiché** (pas d'écran
  d'erreur, pas de flash) ; elle se rattrape au poll suivant.
- Données partielles (ex. enjeu indisponible) : la zone concernée est masquée,
  jamais de placeholder d'erreur visible du public.

## États limites

| Situation | Comportement |
|---|---|
| Aucune édition active | Carousel réduit à la slide Tournoi avec la marque et l'horloge (état neutre). |
| Édition active sans aucun match | Slide Tournoi seule (les autres sont sautées). |
| Match de poule LIVE sans classement résolu | Scoreboard sans panneau d'enjeu (masqué). Un match de tableau affiche toujours sa phase (dérivée de `stage`, jamais indisponible). |
| Match en échauffement sans affiche | Fond de court + bloc central seul (ÉCHAUFFEMENT, compte à rebours, joueurs, étape/court) — pas de noms en très grand. |
| Fin de match : le fetch one-shot échoue | Pas de scène vainqueur, carousel direct (jamais d'erreur visible). |
| Deux matchs LIVE (état anormal) | Le serveur choisit le hero (featured puis plus récent, voir [[tv-state]]) ; la TV n'affiche jamais deux scores. |

## Données

- **Polling** (voir [[tv-state]]) : état chaud `GET /api/tv/state/` à **~2 s**
  (score point par point) ; contenu froid `GET /api/tv/idle/` à **~10 s**
  (slides). Les timers passent par `usePolling` (pause onglet caché comprise —
  sans effet sur une TV, mais convention unique).
- Lecture **publique** (`meta.public`), aucune mutation depuis cet écran.
- `/` et toute route inconnue redirigent vers `/tv/live` (existant, conservé).

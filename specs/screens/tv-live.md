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
bascule **automatiquement** entre deux états :

- **SCOREBOARD** dès qu'un match est `LIVE` : le score en grand + l'enjeu du
  match + le bandeau « À suivre » ;
- **CAROUSEL** sinon : rotation de slides d'information (stats, résultats,
  poules, tableau, programme, annonces).

La bascule est **dérivée** de l'état serveur (`hero` non nul ⇄ nul, voir
[[tv-state]]) — jamais d'action manuelle. La scène est fixée à 1920×1080 et
mise à l'échelle sur l'écran réel (`TvLayout` / `useScale`).

---

## État SCOREBOARD (un match est LIVE)

### En-tête

- Marque du tournoi (« OPEN DE MOUTILLOUX · ÉDITION {année} »).

### Bande de score (bas d'écran)

- Ligne titre : pastille « EN DIRECT » + intitulé de l'étape (`stageLabel` :
  « Match de poule — Poule A », « Demi-finale »…) + badge « JEU DÉCISIF » si
  tie-break en cours.
- Par joueur : nom (nom d'équipe en Double), balle de service côté serveur,
  **sets terminés** (boîtes par set, depuis `setScores`), **jeux** du set en
  cours, **points** du jeu en cours (0/15/30/40/AV, points bruts en tie-break).
- Pied de bande : court, durée du match (`clock`), horloge (`now`).

### Fond de scène : l'affiche du match

Si le match a une **affiche générée** (`hero.posterUrl`, voir
[[affiche-match]]), elle remplace le fond de court sur toute la scène — son
visuel réserve par conception la zone basse à la bande de score. Sans affiche,
le fond de court actuel demeure.

### Zone d'enjeu (centre de l'écran)

Le grand fond n'est plus vide : il accueille l'**enjeu du match**
(décision 4 de [[tv-map]]), affiché **par-dessus l'affiche** le cas échéant,
dans un panneau semi-transparent (l'affiche reste lisible derrière) :

- **Match de poule** → le **classement de la poule** des deux joueurs
  (standings : rang, nom, V/D, points, badge Q), les deux joueurs du match mis
  en évidence. Le public voit ce que le match peut changer.
- **Match de tableau** (QF/SF/F/P3) → le **mini-tableau** de l'épreuve, le
  match en cours mis en évidence (le chemin vers la finale).
- Données fournies par [[tv-state]] (`stake`) ; si l'enjeu n'est pas
  disponible (données pas prêtes), la zone reste sobre (fond de court seul) —
  jamais d'erreur visible.

### Bandeau « À suivre »

Au-dessus de la bande de score, **uniquement s'il existe un next** (défini par
[[tv-state]]) :

- « À SUIVRE — {A} vs {B} · {étiquette de poule/étape} » + mention d'appel
  (« Joueurs suivants, présentez-vous au juge-arbitre »).
- But : laisser les joueurs suivants se préparer pendant le match en cours.

---

## État CAROUSEL (aucun match LIVE)

### Cadre

- En-tête : marque + horloge (`now`).
- Pied : barre « PROCHAIN MATCH » (~heure, joueurs, à partir du *next* — masquée
  s'il n'y a pas de next, remplacée par « Programme du tournoi en cours de
  préparation ») + pastilles de pagination des slides.
- Rotation automatique : **~8 s par slide**, fondu. Une slide **sans contenu
  est sautée** (décision 5). Les pastilles reflètent les slides réellement
  affichables.

### Slides (dans cet ordre)

| Slide | Contenu | Vide ⇒ sautée si |
|---|---|---|
| **Tournoi** | Stats agrégées de l'édition : matchs joués / total, inscrits, épreuves — et le statut (« EN ATTENTE DU PROCHAIN MATCH »). | jamais (slide par défaut) |
| **Derniers résultats** | Les **5 derniers matchs terminés** de l'édition (ordre `finished_at` décroissant — pas l'ordre calendaire), toutes épreuves : étape, joueurs (vainqueur en évidence), score par sets. | aucun match terminé |
| **Poules** | Les poules d'**une épreuve** (lettre, standings V/D/Pts, badge Q) — **rotation par épreuve** : au passage suivant de la slide, l'épreuve suivante qui a des poules (décision 6). L'épreuve est nommée dans le titre. | aucune poule composée |
| **Tableau** | Le tableau final d'**une épreuve** (QF→SF→F, + 3e place si l'épreuve l'active), étiquettes de provenance sur les places vides — même rotation par épreuve. | aucun tableau créé |
| **Programme** | Les **N prochains matchs planifiés** (N ≈ 4–6) à partir du *next*, dans l'ordre de la séquence : ~heure, joueurs, étiquette de poule ; le premier marqué « bientôt ». Pied : « Horaires estimés — susceptibles de bouger ». **Journée courante épuisée** → titre « Programme de demain » et matchs de la journée suivante ; plus aucune journée → « Programme terminé » (slide affichée une fois puis sautée). | aucun match planifié restant |
| **Annonces** | Les annonces **actives** de l'édition (voir [[tv-state]], modèle `Announcement`), en texte grand format. | aucune annonce active |
| **Affiche** | L'**affiche du prochain match** (`posterUrl` du next, voir [[affiche-match]]) en grand, avec ~heure et joueurs — effet « à l'affiche ». | le next n'a pas d'affiche |

Toutes les heures publiques sont **approximatives** (préfixe `~`, décision 18
d'[[admin-panel-map]] / [[planning]]).

---

## Bascule d'état

1. Le front polle l'état TV (~2 s, voir Données). `hero` non nul → SCOREBOARD ;
   nul → CAROUSEL.
2. La bascule est immédiate (au poll suivant), sans transition bloquante ; le
   carousel reprend sa rotation là où il s'était arrêté.
3. Un match mis « à l'antenne » depuis l'admin ([[admin-matchs]], mise en
   avant) devient le `hero` : même mécanique, aucune logique TV spécifique.

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
| Match LIVE sans poule ni tableau résolus | Scoreboard sans zone d'enjeu (fond de court sobre). |
| Deux matchs LIVE (état anormal) | Le serveur choisit le hero (featured puis plus récent, voir [[tv-state]]) ; la TV n'affiche jamais deux scores. |

## Données

- **Polling** (voir [[tv-state]]) : état chaud `GET /api/tv/state/` à **~2 s**
  (score point par point) ; contenu froid `GET /api/tv/idle/` à **~10 s**
  (slides). Les timers passent par `usePolling` (pause onglet caché comprise —
  sans effet sur une TV, mais convention unique).
- Lecture **publique** (`meta.public`), aucune mutation depuis cet écran.
- `/` et toute route inconnue redirigent vers `/tv/live` (existant, conservé).

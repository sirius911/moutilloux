---
type: screen
module: tv/programme
fichiers:
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvLayout.vue
  - live/api_views.py
---

# Spec fonctionnelle — Programme TV & bandeau « À suivre »

## Rôle

Face **publique** du calendrier ([[admin-matchs]], [[planning]]) sur la TV.
Lecture seule, pensée « affichage » : les joueurs et le public voient **qui joue
bientôt**. Deux points de contact, **greffés sur l'existant** (décision 20 de
[[admin-panel-map]]) — pas de nouvel écran :

1. une **slide « Programme »** dans le carousel public ;
2. un **bandeau « À suivre »** sur le scoreboard du match en cours.

Aucune heure n'est saisie ; les horaires sont **estimés** et affichés
**approximatifs** (`~HH:MM`) — voir [[planning]]. Le public n'est jamais invité à
prendre l'heure au pied de la lettre.

---

## Slide « Programme » (carousel)

S'insère comme une slide du carousel TV, au même titre que Scores / Poules /
Tableau, sur la rotation existante ([TvIdle.vue](../../frontend/app/src/views/tv/TvIdle.vue)).

- Titre « Prochains matchs ».
- Liste des **N prochains matchs planifiés** de la journée courante (N ≈ 4–6), dans
  l'ordre de la séquence, **à partir du *next*** :
  - **~heure** estimée (préfixe `~`) ;
  - « {A} vs {B} » ;
  - étiquette de poule.
- Le premier de la liste (le *next*) porte un marqueur **« bientôt »**.
- Pied : rappel « horaires estimés, susceptibles de bouger » + indicateur de slide
  (pastilles du carousel).
- Rotation : cadence du carousel existant ; le contenu se rafraîchit par polling
  (~4 s).

---

## Bandeau « À suivre » (scoreboard)

Sur le scoreboard du match **en cours**
([TvScoreboard.vue](../../frontend/app/src/views/tv/TvScoreboard.vue)), un bandeau
bas annonce le **prochain match** (le *next* de la séquence) :

- « À suivre — {A} vs {B} · Poule {X} » (+ mention d'appel des joueurs).
- But : laisser les joueurs suivants se préparer pendant le match en cours.
- Présent **uniquement** s'il existe à la fois un match en cours **et** un next.

---

## Données

- Lecture **publique** (routes `/tv/*`, `meta.public` — voir [[admin-shell]] pour la
  séparation public / admin).
- Source : packer « calendrier » / état TV enrichi (voir [[planning]], « contrat
  d'API »). Le *next* et les *N prochains* sont **dérivés** côté serveur ou front à
  partir de la séquence — jamais stockés.
- Polling TV ~4 s ; aucune mutation depuis ces surfaces.

## États limites

| Situation | Comportement |
|---|---|
| Aucun match planifié | Slide Programme : « Aucun match programmé » (ou la slide est sautée par la rotation). |
| Aucun match en cours | Pas de bandeau « À suivre » : le scoreboard montre son état au repos habituel. |
| Match en cours sans next | Bandeau « À suivre » masqué. |
| Journée terminée | La slide bascule sur la journée suivante si elle existe, sinon « Programme terminé ». |

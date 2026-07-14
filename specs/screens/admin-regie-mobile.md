---
type: screen
module: admin/regie-mobile
fichiers:
  - frontend/app/src/router/index.ts
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/src/stores/event.ts
  - frontend/app/src/stores/live.ts
  - live/api_views.py
  - live/admin_views.py
---

# Spec fonctionnelle — Régie mobile (admin)

## Rôle de l'écran

`/admin/regie` (garde `isAdmin`) est la surface **téléphone** de
l'organisateur : les **gestes chauds** qui se font debout, au bord du court,
pendant que le tournoi se joue. Ce n'est **pas** l'admin complet — la
préparation (poules, seeding, drag du calendrier, affiches) reste desktop
(voir [[mobile]]).

Scène mobile portrait (socle : [[mobile]]). **Aucun endpoint neuf** : l'écran
réutilise les services et endpoints existants du calendrier, du match et des
annonces.

---

## Éléments d'interface

### Le fil de la journée

- La **journée courante** du calendrier (même source que le programme arbitre :
  séquence ordonnée matchs + pauses), en liste verticale.
- Par ligne : heure estimée `~HH:MM` (réelle si terminé), puce d'état
  (Terminé / En cours / Next / Planifié), **teinte de ponctualité**
  (vert / orange / rouge, heuristique simplifiée ci-dessous), joueurs
  (ou étiquettes de provenance), étape.
- **Teinte de ponctualité — heuristique simplifiée propre à cet écran**
  (arbitrage 2026-07-14, #412 ; décision initiale plan #340 § 3). La régie
  n'applique **pas** le moteur ETA ni les règles de l'« Indicateur de
  ponctualité » de [[planning]], dont la surface est le calendrier admin
  ([[admin-matchs]]). Elle compare l'heure actuelle à l'heure planifiée
  affichée du match (`scheduledTime`, préfixe `~` ignoré, ancrée sur la date
  de la journée courante), pour les seuls matchs `SCHEDULED` :
  - **vert** — heure planifiée pas encore dépassée ;
  - **orange** — dépassée de 0 à 15 min ;
  - **rouge** — dépassée de plus de 15 min.
  `LIVE`, `FINISHED`, `CANCELED` : aucune teinte — le match en cours est de
  toute façon épinglé hors du fil. Limite assumée : les heures au-delà de
  minuit (arbitrage #397, [[planning]]) ne sont pas gérées par cette
  heuristique — un match planifié après minuit peut se teinter à tort en
  fin de soirée.
- Le match **en cours** est épinglé en tête avec son score live (sets, jeux,
  points — depuis `_pack_match`, mêmes règles d'affichage que partout :
  `displayPointA/B`).
- **Lecture seule pour l'ordre** : pas de drag-and-drop sur mobile — le
  réordonnancement se fait au desktop.

### Actions par match (feuille d'actions)

Taper une ligne ouvre une feuille d'actions contextuelles — chacune réutilise
un service existant ([[cycle-de-vie-match]]) avec les mêmes gardes et
confirmations que sur desktop :

| Action | Condition | Service |
|---|---|---|
| **Démarrer** (→ échauffement) | `SCHEDULED`, slots résolus | `démarrer` (confirmation si un autre match est en cours) |
| **Mettre à l'antenne** | `SCHEDULED` | mise en avant (même confirmation que [[admin-matchs]]) |
| **Terminer** (vainqueur, bascule abandon) | `LIVE` | `terminer` |
| **Forfait** | `SCHEDULED` | `forfait` |
| **Annuler** | `SCHEDULED`/`LIVE` | `annuler` (confirmation « irréversible ») |
| **Correction rapide de score** | `LIVE`/`FINISHED` | l'édition de score existante (`matches/edit`), en formulaire compact |
| **Rouvrir** | `FINISHED` | `rouvrir` (admin seul) |

### Annonces TV

- Section « Annonces » : lister les annonces de l'édition, **activer /
  désactiver**, **ajouter** (texte court), **supprimer** — le CRUD existant de
  [[tv-state]], en interface compacte.

---

## Gestion des erreurs

- Toute action refusée par le serveur affiche **le message JSON renvoyé**
  (toast), conformes à [[erreurs-api]]. Jamais d'échec silencieux.

## États limites

| Situation | Comportement |
|---|---|
| Aucune édition active / aucune journée | État vide avec renvoi au desktop (« Configurez le tournoi depuis un ordinateur »). |
| Journée courante épuisée | Bascule sur la journée suivante (même règle que le *next*, [[tv-state]]). |
| Consulté depuis un desktop | L'écran fonctionne (scène scalée) mais n'est pas mis en avant dans la navigation desktop. |

## Données & temps réel

- Même polling que les surfaces temps réel (~2 s sur le match live, ~5 s sur le
  fil de journée — `usePolling`, pause onglet caché).
- Après chaque action : re-fetch immédiat (même convention que
  [[arbitre-match]]).

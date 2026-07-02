---
type: screen
module: arbitre/home
fichiers:
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/stores/auth.ts
  - frontend/app/src/composables/usePolling.ts
  - frontend/app/src/composables/useApi.ts
  - live/api_views.py
  - live/models.py
---

# Spec fonctionnelle — Accueil Arbitre (la file)

## Rôle de l'écran

L'accueil arbitre (`/arbitre`) est le **poste de pilotage** de l'arbitre : la **file
des matchs** du tournoi, dans laquelle il pioche le match à jouer. C'est un écran
tablette (iPad), pensé pour un coup d'œil rapide entre deux rencontres.

> **File partagée, pas d'affectation.** Tout arbitre connecté voit la **même** file
> (les matchs de l'édition active) — il n'y a **pas** de désignation nominative
> arbitre → match. Cohérent avec le modèle **court central unique** ([[cycle-de-vie-match]])
> et le grain édition. L'arbitre arbitre « ce qui vient ».

L'écran ne modifie aucun statut : il **navigue** vers l'écran de saisie
([[arbitre-match]]), où le match se démarre et se joue. Le cycle de vie d'un match
(états, transitions, qui peut quoi) est décrit dans [[cycle-de-vie-match]].

---

## Éléments d'interface

### En-tête

- **Salutation** : « Bonjour {username}, » + sous-titre « Vous êtes l'arbitre désigné
  · {N} match(s) en cours » (N = nombre de matchs `LIVE`).
- **Bouton Déconnexion** : ferme la session et renvoie vers [[login]].

### Onglets de filtre

Quatre onglets, chacun avec un **compteur** :

| Onglet | Contenu | Indice |
|---|---|---|
| **Tous** | tous les matchs de la file | — |
| **En direct** | `LIVE` | pastille rouge pulsée si ≥ 1 |
| **À venir** | `SCHEDULED` | — |
| **Terminés** | `FINISHED` | — |

Les matchs `CANCELED` **n'apparaissent pas** dans la file arbitre (ils sont gérés
côté admin, colonne « Annulés » — [[admin-matchs]]).

### Liste de matchs

Cartes ordonnées **comme le calendrier** (matchs actifs `LIVE`+`SCHEDULED` par
`order_index`, puis les derniers `FINISHED`). Chaque carte affiche :

- **Bandeau d'état** coloré (accent = en direct, neutre = terminé).
- **Puce d'état** : EN DIRECT (point pulsé) / PRÉVU / TERMINÉ.
- **Heure estimée** et **court** (« Central ») quand disponibles.
- **{Joueur A} vs {Joueur B}** (ou étiquette de provenance « A1 / C2 » si le joueur
  n'est pas encore résolu — matchs de tableau).
- **Étape** (poule / quart / demi / finale) et, pour un match `LIVE`, le **score
  courant** abrégé (sets joués + jeux en cours).
- **Appel à l'action** selon l'état :

| État | Libellé | Effet du clic |
|---|---|---|
| `SCHEDULED` | **Démarrer** | ouvre [[arbitre-match]] (le démarrage réel, avec confirmation, s'y fait) |
| `LIVE` | **Reprendre** | ouvre [[arbitre-match]] sur le match en cours |
| `FINISHED` | **Voir** | ouvre [[arbitre-match]] en lecture seule |

> Le clic **navigue** toujours vers l'écran de saisie ; il ne déclenche aucune
> transition directement depuis la liste. Le passage `SCHEDULED → LIVE` (et sa
> confirmation si un autre match est en cours) appartient à [[arbitre-match]].

### Pied de page

Indicateur de **synchronisation** : « Synchronisé · {HH:MM:SS} » avec un point de
statut, mis à jour à chaque rafraîchissement.

---

## Données & temps réel

- Source : `GET /api/arbitre/matches/` — matchs actifs (`LIVE` + `SCHEDULED`, triés
  `order_index`) suivis des **20 derniers `FINISHED`**, tous packés via `_pack_match`.
- **Rafraîchissement périodique** ~5 s (`usePolling`), pour refléter les passages
  En direct / Terminé et l'ordre recalé par l'admin. La liste et l'horloge de
  synchronisation se mettent à jour ensemble.
- **Pause onglet caché** : le polling se suspend quand l'onglet n'est pas visible
  (`usePolling`, `visibilitychange`) et reprend au retour.
- **Auth** : l'endpoint **doit** exiger le rôle arbitre (`@referee_required`).
  *(⚠ Aujourd'hui `@login_required` seul — tout compte connecté y accède ;
  à durcir, voir [[cycle-de-vie-match]].)* La route `/arbitre/*` est déjà gardée par
  `requiresReferee` côté front ([[routing-context]]).

---

## États limites

| Situation | Comportement |
|---|---|
| Filtre sans match | « Aucun match dans cette catégorie. » |
| Aucune édition active | Liste vide (l'endpoint renvoie `[]`). |
| Match sans joueurs résolus | La carte affiche les étiquettes de provenance ; le clic reste possible (démarrage géré à l'écran match). |

## Gestion des erreurs

- Un échec de chargement laisse la dernière liste connue affichée ; le point de
  synchronisation reflète l'échec. Pas de bandeau bloquant (l'écran est en polling,
  la tentative suivante suit). Une session expirée renvoie vers [[login]] :
  `useApi` détecte la redirection Django vers `/accounts/login` et bascule sur
  `/login` (déjà en place).

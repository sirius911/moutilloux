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

# Spec fonctionnelle — Accueil Arbitre (le programme)

## Rôle de l'écran

L'accueil arbitre (`/arbitre`) est le **poste de pilotage** de l'arbitre : le
**miroir en lecture seule du calendrier** de l'édition ([[admin-matchs]],
[[planning]]), pour voir d'un coup d'œil **quel match lancer maintenant** et ce
qui suit. C'est un écran tablette (iPad), pensé pour un coup d'œil rapide entre
deux rencontres.

> **Programme partagé, pas d'affectation.** Tout arbitre connecté voit le
> **même** programme (les matchs de l'édition active) — il n'y a **pas** de
> désignation nominative arbitre → match. Cohérent avec le modèle **court
> central unique** ([[cycle-de-vie-match]]) et le grain édition. L'arbitre
> arbitre « ce qui vient ».

L'écran ne modifie aucun statut : il **navigue** vers l'écran de saisie
([[arbitre-match]]), où le match se démarre et se joue. Le cycle de vie d'un match
(états, transitions, qui peut quoi) est décrit dans [[cycle-de-vie-match]].

Remplace l'ancienne file à quatre onglets (Tous / En direct / À venir /
Terminés) : plus d'onglets — la structure de l'écran **est** celle du
calendrier.

---

## Éléments d'interface

### En-tête

- **Salutation** : « Bonjour {username}, » + sous-titre « Vous êtes l'arbitre désigné
  · {N} match(s) en cours » (N = nombre de matchs `LIVE`).
- **Bouton Déconnexion** : ferme la session et renvoie vers [[login]].

### Bloc « À l'instant » (en tête de page)

- Le match **`LIVE`** de l'édition, s'il existe : carte proéminente, score
  courant abrégé, action **Reprendre**.
- Sinon, le **Next** (définition unique de [[tv-state]] / [[planning]]) :
  carte proéminente « Prochain match », ~heure estimée, action **Démarrer**
  bien visible. C'est le chemin nominal : l'arbitre lance le bon match sans
  chercher.
- Ni LIVE ni next : le bloc est masqué.

### Journées (le programme)

Sous le bloc « À l'instant », **toutes les journées** de l'édition, empilées
comme sur le calendrier admin :

- La **journée courante** est dépliée et mise en évidence ; les autres
  (passées et à venir) sont **repliables** (dépliées d'un tap sur leur
  en-tête).
- En-tête de journée : nom + date, nombre de matchs, « début HH:MM » (lecture
  seule — les bornes se règlent côté admin).
- Dans chaque journée, les lignes dans l'**ordre de la séquence**
  (`order_index`), **pauses comprises** (bandes discrètes, lecture seule) :

| Élément de ligne | Contenu |
|---|---|
| Heure | `~HH:MM` estimée (heure réelle, sans tilde, si terminé) |
| Puce d'état | EN DIRECT (point pulsé) / NEXT / PRÉVU / TERMINÉ |
| Affiche | {Joueur A} vs {Joueur B} (ou étiquettes de provenance « A1 / C2 » si non résolus) + étape (poule / quart / demi / finale) |
| Score | pour un match `LIVE`, score courant abrégé (sets joués + jeux en cours) |
| Action | **Démarrer** (`SCHEDULED`) / **Reprendre** (`LIVE`) / **Voir** (`FINISHED`) |

- Les matchs **terminés restent à leur place** dans la journée, atténués.
- Les matchs `CANCELED` **n'apparaissent pas** (gérés côté admin, colonne
  « Annulés » — [[admin-matchs]]). La pile « à planifier » n'apparaît pas non
  plus : l'arbitre ne voit que la séquence ordonnée (un match non planifié
  reste jouable, mais il se lance alors depuis l'admin — cas hors nominal).

> Le clic **navigue** toujours vers l'écran de saisie ; il ne déclenche aucune
> transition directement depuis la liste. Le passage `SCHEDULED → LIVE` (avec
> choix du premier serveur, et confirmation si un autre match est en cours)
> appartient à [[arbitre-match]].

### Pied de page

Indicateur de **synchronisation** : « Synchronisé · {HH:MM:SS} » avec un point de
statut, mis à jour à chaque rafraîchissement.

---

## Données & temps réel

- Source : `GET /api/arbitre/matches/` — **enrichi en lecture calendrier** : les
  journées de l'édition avec leur séquence ordonnée (matchs + pauses, matchs
  packés via `_pack_match`) et le **next** (réutilise le packer calendrier de
  [[planning]] et la définition unique du next de [[tv-state]] — pas de
  troisième forme).
- **Rafraîchissement périodique** ~5 s (`usePolling`), pour refléter les passages
  En direct / Terminé, l'ordre recalé par l'admin et les heures estimées. La
  liste et l'horloge de synchronisation se mettent à jour ensemble.
- **Pause onglet caché** : le polling se suspend quand l'onglet n'est pas visible
  (`usePolling`, `visibilitychange`) et reprend au retour.
- **Auth** : l'endpoint exige le rôle arbitre (`@referee_required`, voir
  [[cycle-de-vie-match]]). La route `/arbitre/*` est déjà gardée par
  `requiresReferee` côté front ([[routing-context]]).

---

## États limites

| Situation | Comportement |
|---|---|
| Aucune journée configurée | État vide : « Aucun programme pour le moment » (les journées se créent côté admin). |
| Journée sans match | Section vide, repliée par défaut. |
| Aucune édition active | Écran vide (l'endpoint renvoie une structure vide). |
| Match sans joueurs résolus | La ligne affiche les étiquettes de provenance ; le clic reste possible (démarrage géré à l'écran match). |

## Gestion des erreurs

- Un échec de chargement laisse la dernière liste connue affichée ; le point de
  synchronisation reflète l'échec. Pas de bandeau bloquant (l'écran est en polling,
  la tentative suivante suit). Une session expirée renvoie vers [[login]] :
  `useApi` détecte la redirection Django vers `/accounts/login` et bascule sur
  `/login` (déjà en place).

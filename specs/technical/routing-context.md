---
type: technical
module: routing
fichiers:
  - frontend/app/src/router/index.ts
  - frontend/app/src/stores/event.ts
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminBracket.vue
---

# Spec technique — Contexte de routage (épreuve dans l'URL)

> Comment l'admin sait **quoi charger** au montage et au rechargement. Source de
> vérité du contexte des écrans dépendants d'une épreuve. Les specs d'écran
> décrivent l'UI ; celle-ci décrit d'où vient l'épreuve active et comment elle
> survit à un rechargement ou à un partage de lien.

## Problème résolu

Deux notions de contexte coexistent (vocabulaire fixé par [[admin-panel-map]] et
[[admin-tournoi]]) :

| Contexte | Nature | Persistance |
|---|---|---|
| **Édition active** | bascule **globale** — toute l'app (admin, arbitre, TV) travaille dessus | en base (`TournamentEdition.is_active`), renvoyée par `GET /api/editions/` |
| **Épreuve active** | choix d'affichage des écrans **Inscriptions / Poules / Planning / Tableau final** | **portée par l'URL** (cette spec) |

Avant cette spec, l'épreuve active vivait **uniquement en mémoire** (`activeEventId`
dans le store). Au rechargement, `fetchEditions` la réinitialisait à `events[0]` :
l'admin perdait son contexte et pouvait se retrouver sur une autre épreuve que celle
qu'il consultait. L'**URL** devient la source de vérité pour lever ce défaut.

## Schéma d'URL

Décision 22 de [[admin-panel-map]] : l'épreuve active est un **segment de chemin**.

| Écran | Route | Portée |
|---|---|---|
| Tournoi | `/admin/tournoi` | édition (aucun param d'épreuve) |
| Joueurs (registre) | `/admin/players` | global (aucun param) |
| Inscriptions | `/admin/events/:eventId/inscriptions` | épreuve |
| Poules | `/admin/events/:eventId/groups` | épreuve |
| Planning (calendrier) | `/admin/events/:eventId/matches` | épreuve |
| Tableau final | `/admin/events/:eventId/bracket` | épreuve |

`:eventId` est l'identifiant numérique de l'épreuve active. `/admin` redirige vers
`/admin/tournoi` (défaut inchangé).

**Cas du Planning.** Le calendrier est mono-court et **couvre toute l'édition**
(toutes épreuves confondues, voir [[planning]]) : la donnée se charge par édition
(`fetchCalendar(editionId)`), l'édition étant dérivée de l'épreuve d'URL
(`event.editionId`). Le `:eventId` reste présent pour rester homogène avec les
autres écrans et pour cibler les actions **par épreuve** (générer les matchs,
pré-poser) ainsi que la mise en évidence.

## Source de vérité et miroir dans le store

1. **L'URL fait foi.** `route.params.eventId` est la vérité de l'épreuve active.
2. Le store **reflète** l'URL : `activeEventId` est synchronisé *depuis* la route
   (watcher de route porté par le shell admin), jamais l'inverse. Les écrans
   continuent de lire `activeEventId` / les actions du store comme aujourd'hui.
3. L'**édition active** reste lue du serveur (`data.activeEdition`) et n'est pas
   dans l'URL (voir « Hors périmètre »).

## Sélecteur d'épreuve

Le sélecteur en en-tête de page (décision 16, [[admin-shell]]) **ne mute plus le
store** directement. Il **navigue** : `router.push` vers le même écran en
remplaçant `:eventId`. Le store se met à jour via le watcher de route. Conséquence :
le choix d'épreuve se **conserve d'un écran à l'autre** (les liens de navigation
portent l'épreuve courante) et **survit au rechargement** (il est dans l'URL).

## Liens de navigation (sidebar)

Les entrées de sidebar des écrans dépendants pointent vers l'épreuve **active
courante** : `/admin/events/${activeEventId}/groups`, etc. Tant qu'aucune épreuve
n'est résolue (chargement à froid), la cible est résolue après `fetchEditions`. Les
entrées indépendantes (Tournoi, Joueurs) restent sans param.

## Garde de route et résolution du défaut

À l'entrée d'une route à épreuve (garde de navigation ou résolution au montage du
shell) :

1. **Charger les éditions** si ce n'est pas déjà fait (`fetchEditions`).
2. **`:eventId` absent** → rediriger vers l'épreuve par défaut : la **première
   épreuve de l'édition active**.
3. **`:eventId` inconnu** (n'appartient pas aux épreuves de l'édition active —
   identifiant périmé, supprimé, ou d'une autre édition) → rediriger vers l'épreuve
   par défaut (lien profond périmé rattrapé silencieusement).
4. **Aucune épreuve dans l'édition active** → afficher l'**état vide « Aucune
   épreuve active »** (lien vers Tournoi) ; pas de redirection possible.

Ces règles garantissent qu'un lien partagé/bookmarké pointant vers une épreuve
disparue n'aboutit jamais à un écran cassé.

## Comportements clés

| Scénario | Résultat attendu |
|---|---|
| **Rechargement** (F5) sur un écran d'épreuve | la même épreuve est rechargée (lue dans l'URL) — défaut corrigé |
| **Lien partagé / bookmark** `/admin/events/42/groups` | ouvre les poules de l'épreuve 42 (si valide pour l'édition active) |
| **Changer d'épreuve** dans le sélecteur | `router.push` ; l'URL et les données changent ; pas de rechargement de page |
| **Naviguer** d'un écran d'épreuve à un autre | l'épreuve courante est conservée (liens porteurs du `:eventId`) |
| **Activer une autre édition** (écran Tournoi) | bascule globale serveur ; l'épreuve par défaut de la nouvelle édition est re-résolue et l'URL redirigée |
| **Écrans indépendants** (Tournoi, Joueurs) | inchangés par un changement d'épreuve |

## API

Aucun nouvel endpoint. La résolution repose sur l'existant `GET /api/editions/`
(`{ activeEdition, events, editions }`) pour connaître l'édition active et la liste
de ses épreuves, puis les endpoints `…/events/<id>/…` déjà en place.

## Hors périmètre (itération suivante éventuelle)

- **Édition dans l'URL.** L'édition reste une bascule globale serveur ; consulter
  une édition **non active** via l'URL (`/admin/editions/:editionId/…`) n'est pas
  couvert ici. Le schéma à segment de chemin est extensible dans ce sens si le
  besoin émerge (arbitrer alors URL vs `is_active`).
- **Espaces Arbitre et TV.** Inchangés : l'arbitre route déjà par `:matchId`, la TV
  est publique et suit l'édition active globale.

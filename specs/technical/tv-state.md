---
type: technical
module: tv-state
fichiers:
  - live/api_views.py
  - live/views.py
  - live/models.py
  - competition/models.py
  - frontend/app/src/stores/live.ts
  - frontend/app/src/types/index.ts
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
---

# Spec technique — État TV (contrat de données)

> Le contrat de données de l'écran [[tv-live]] : deux endpoints publics, une
> seule définition du *next*, le modèle des annonces et les retraits legacy.
> Source de vérité du « d'où vient ce que la TV affiche ».

## Problème résolu

Aujourd'hui la TV vit sur **deux contrats incompatibles** :

- `GET /api/score_state/` (`live/views.py`, pré-SPA) sérialise en snake_case,
  renvoie `side_a`/`side_b` en chaînes, sans `setScores` — alors que le front
  le type comme un `Match` camelCase : **le scoreboard n'affiche rien de
  correct pendant un match LIVE** ;
- `GET /api/tv/upcoming/` utilise `_pack_match` (correct), et **écrase le même
  ref `next`** du store avec une autre forme — le bandeau « À suivre »
  clignote au rythme des polls ;
- le serveur a **deux définitions du next** (`get_next_match` : premier
  `SCHEDULED` de l'édition, toutes journées ; `api_tv_upcoming` : journée
  courante).

Cette spec unifie tout sur `_pack_match` (convention CLAUDE.md §5) et une
seule définition du next.

---

## Définition unique du « next »

> Le *next* est le **premier match `SCHEDULED` de la séquence de la journée
> courante** (plus petit `order_index` de la journée), le match `LIVE` ne
> comptant pas. Journée courante = la première `PlayDay` de date ≥ aujourd'hui
> qui a encore des matchs `SCHEDULED` ordonnés ; à défaut, il n'y a **pas de
> next** (jamais de repli sur un match hors séquence ou d'une journée passée).

Cohérent avec [[planning]] (« États dérivés — Next ») et calculé **côté
serveur**, en un seul endroit, consommé par le scoreboard (« À suivre »), le
footer du carousel et la slide Programme.

---

## `GET /api/tv/state/` — l'état chaud (pollé ~2 s)

Lecture publique. Tout match est packé par `_pack_match`.

```jsonc
{
  "editionYear": 2026,            // édition active (null si aucune)
  "now": "15h42",                 // horloge serveur locale
  "hero": { …_pack_match… },      // le match LIVE, ou null
  "next": { …_pack_match… },      // le next (définition ci-dessus), ou null
  "stake": {                      // l'enjeu du hero, ou null
    // hero en poule :
    "kind": "group",
    "groupName": "A",
    "eventName": "Simple Homme",
    "standings": [ { "rank", "name", "wins", "losses", "points",
                     "qualified", "entryId" } ],
    // OU hero en tableau :
    "kind": "bracket",
    "eventName": "Simple Homme",
    "bracket": { …même format que GET /api/events/<id>/bracket/… }
  }
}
```

- **Choix du hero** : match `LIVE` de l'édition active, tri `-is_featured,
  -updated_at` (existant — gère le cas anormal de deux LIVE).
- `stake` est **dérivé du hero** (sa poule ou le tableau de son épreuve) ;
  `null` si non résolvable. Les deux entries du hero sont identifiables dans
  les standings via `entryId`.
- `qualified` n'est vrai que si la **poule est terminée** (plus aucun match
  `SCHEDULED`/`LIVE` dans la poule) — jamais sur classement partiel (voir
  [[cycle-de-vie-epreuve]]). Même règle pour les standings de `tv/idle`.

## `GET /api/tv/idle/` — le contenu froid (pollé ~10 s)

Lecture publique. Alimente les slides du carousel ([[tv-live]]) :

```jsonc
{
  "stats": { "matchesFinished", "matchesTotal", "entriesCount",
             "eventsCount" },                       // slide Tournoi
  "recentResults": [ …_pack_match… ],               // 5 FINISHED, finished_at desc
  "events": [                                       // rotation par épreuve
    { "id", "name",
      "groups": [ { "id", "name", "standings": [...] } ],   // vide si aucune
      "bracket": { …format bracket… } | null }              // null si aucun
  ],
  "programme": {
    "day": "today" | "tomorrow" | "finished",       // bascule de journée (décision 8)
    "playDay": { …_pack_play_day… } | null,
    "upcoming": [ …_pack_match… ]                   // N ≤ 6, à partir du next
  },
  "announcements": [ { "id", "message" } ]          // actives, ordre de création
}
```

- `programme.day` : `today` si la journée courante a encore des matchs ;
  `tomorrow` si elle est épuisée mais qu'une journée suivante existe ;
  `finished` sinon (`upcoming` vide).
- `events` ne contient que les épreuves de l'édition active ; les slides
  sautent celles sans contenu (champ vide/null).
- Coût maîtrisé : cet endpoint remplace le polling TV de `GET /api/editions/`
  (dont les agrégats `_pack_edition` sont chers) — la TV ne consomme plus
  aucun endpoint admin.

## Modèle `Announcement` (à créer)

| Champ | Type | Rôle |
|---|---|---|
| `edition` | FK `TournamentEdition` | l'édition |
| `message` | Text | le texte affiché |
| `is_active` | bool (défaut vrai) | diffusée ou non |
| `created_at` | DateTime auto | ordre d'affichage |

- **CRUD admin** : service + endpoints fins (`GET/POST /api/editions/<id>/announcements/…`,
  `edit`/`delete`), conventions back CLAUDE.md §5.
- **Surface UI** : carte « Annonces TV » sur l'écran **Tournoi**
  ([[admin-tournoi]] à compléter au moment de l'implémentation) : lister,
  ajouter, activer/désactiver, supprimer. Pas d'échéance ni de
  programmation horaire (hors périmètre — on active/désactive à la main).

## Front (`stores/live.ts`)

- `fetchTvState()` → `hero`, `next`, `now`, `editionYear`, `stake` (typé).
- `fetchTvIdle()` → `stats`, `recentResults`, `events`, `programme`,
  `announcements`.
- **Un seul écrivain par ref** : `next` n'est plus écrit que par
  `fetchTvState` (fin du flip-flop de formes).
- `fetchScoreState`/`fetchUpcoming` et les types `ScoreState`/`TvUpcoming`
  sont retirés. `fetchMatch` (écran arbitre) est conservé tel quel.

## Retraits (legacy)

| Élément | Sort |
|---|---|
| `GET /api/score_state/` + `score_state`, `get_next_match` (`live/views.py`) | **supprimés** (remplacés par `tv/state`) ; `get_hero_match` déménage/se réutilise côté service |
| `GET /api/tv/upcoming/` | **absorbé** par `tv/idle` (route retirée) |
| Pages publiques Django `results*` (vues + templates + routes) | **supprimées** (décision 2 de [[tv-map]]) |
| Routes SPA `/tv/groups`, `/tv/bracket` + `TvPoules.vue`, `TvBracket.vue` | **supprimés** (décision 1) ; le catch-all continue de rediriger vers `/tv/live` |

## Cadences (récapitulatif)

| Quoi | Endpoint | Cadence |
|---|---|---|
| Score / bascule d'état | `GET /api/tv/state/` | ~2 s |
| Slides du carousel | `GET /api/tv/idle/` | ~10 s |
| Rotation des slides | — (front) | ~8 s |

Les timers passent par `usePolling` (convention unique, pause onglet caché).

## Hors périmètre

- WebSockets / push : le polling reste la règle du projet.
- Programmation horaire des annonces, images/médias dans les annonces.
- Historique des annonces (on supprime, pas d'archive).

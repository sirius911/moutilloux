---
type: overview
module: tv
fichiers:
  - frontend/app/src/views/tv/TvLayout.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/stores/live.ts
  - frontend/app/src/router/index.ts
  - live/views.py
  - live/api_views.py
---

# Cartographie — Espace TV

> Carte de référence de l'espace public TV : sommaire des specs
> (`tv-live.md`, `technical/tv-state.md`) et journal des décisions
> structurantes (brainstorm du 2026-07-04). Le comportement attendu vit dans
> les specs — ce document n'en est que l'index.

## Vue d'ensemble

**Une seule TV physique, un seul court, un seul match à la fois.** L'espace TV
est donc **une seule route publique**, `/tv/live`, qui bascule automatiquement
selon l'état du tournoi :

```
   un match est LIVE ──────►  SCOREBOARD (+ enjeu du match + « À suivre »)
   aucun match LIVE ──────►  CAROUSEL (stats, résultats, poules, tableau,
                                        programme, annonces)
```

La TV est en **lecture seule**, thème sombre, cible 1080p (scène 1920×1080 mise
à l'échelle par `TvLayout`/`useScale`). Elle suit l'**édition active** globale
(`TournamentEdition.is_active`) ; il n'y a pas de notion d'« épreuve active »
côté TV — les slides **tournent sur les épreuves** qui ont du contenu.

| # | Écran | Route | Réf design | Spec |
|---|-------|-------|------------|------|
| 0 | Scène TV (scaling) | `/tv` (layout) | — | couvert par [tv-live.md](./screens/tv-live.md) |
| 1 | TV live (scoreboard ⇄ carousel) | `/tv/live` (défaut, seule route) | `scoreboard.jsx` | ✅ [tv-live.md](./screens/tv-live.md) |

Contrat de données, définition du *next*, annonces et cadences :
[technical/tv-state.md](./technical/tv-state.md).

## User stories (résumé)

- **Spectateur au club** — suivre le score du match en cours de loin ; voir qui
  joue ensuite ; entre deux matchs, voir les classements, le tableau, le
  programme et les annonces de l'organisation.
- **Joueur** — savoir quand il joue (~heure), voir l'enjeu de son match
  (classement de sa poule), se préparer quand son match est annoncé « À
  suivre ».
- **Admin** — n'a *rien* à piloter : la TV suit l'état du tournoi. Seule
  exception : les **annonces libres**, saisies depuis l'admin.

## Décisions structurantes (journal)

1. **Une TV, une route.** `/tv/live` est le canal unique ; l'affichage est
   piloté par l'état (LIVE → scoreboard, sinon carousel). Les routes dédiées
   `/tv/groups` et `/tv/bracket` sont **supprimées** (leurs contenus vivent en
   slides du carousel), ainsi que leurs SFC (`TvPoules.vue`, `TvBracket.vue`).
2. **Le legacy public Django disparaît.** Les pages `results*`
   (`results.html`, `results_live_menu`, `results_poules*`, `results_final*`,
   `results_mix*`) et leurs vues sont retirées ; la SPA est la seule surface
   publique. `GET /api/score_state/` (format snake_case pré-SPA) est
   **remplacé** par le contrat unifié de [[tv-state]] — il était le dernier
   endpoint à ne pas passer par `_pack_match` (convention CLAUDE.md §5).
3. **Une seule définition du « next ».** Celle de [[planning]] : premier match
   `SCHEDULED` de la séquence de la **journée courante**, après le match en
   cours. Les deux implémentations divergentes (`get_next_match` édition-wide,
   `api_tv_upcoming` journée) sont réconciliées côté serveur ([[tv-state]]).
4. **Pendant LIVE : scoreboard + enjeu.** Le score domine (bande basse), et la
   zone centrale montre le **classement de la poule du match en cours** (pour
   un match de tableau : le mini-tableau avec le chemin vers la finale). Le
   bandeau « À suivre » est conservé.
5. **Carousel idle à 6 slides** : Tournoi (stats agrégées — absorbe l'ancienne
   slide « attente »), Derniers résultats, Poules, Tableau, Programme,
   Annonces. Une slide **sans contenu est sautée** par la rotation.
6. **Multi-épreuves : rotation par épreuve.** Les slides Poules et Tableau
   affichent une épreuve à la fois et passent à la suivante au tour d'après.
   Résultats et Programme sont édition-wide (toutes épreuves mélangées, ordre
   chronologique).
7. **Annonces libres** : nouveau modèle `Announcement` (message + actif, par
   édition) géré depuis l'écran **Tournoi** de l'admin ; diffusé en slide (et
   ce sont les seules données TV saisies à la main).
8. **Programme : bascule de journée.** Journée courante épuisée → la slide
   affiche « Programme de demain » (journée suivante) ; plus aucune journée à
   venir → « Programme terminé ».
9. **`tv-programme.md` est absorbée** par [tv-live.md](./screens/tv-live.md)
   (slide Programme + bandeau « À suivre ») ; la spec est retirée.
10. **Pas de têtes de série à l'écran** (décision 3 d'[[admin-panel-map]]
    réaffirmée) : les places vides affichent l'étiquette de provenance
    (« A1 », « WSF1 »…) ou « À désigner » — jamais de « ? ».
11. **Affiches de match IA** (brainstorm du 2026-07-04, intégration de la
    PR #1) : générées et choisies **côté admin** (onglet Affiche du panneau de
    match), stockées sur le match (`Match.poster` → `posterUrl` de
    `_pack_match`). La TV **n'affiche que le résultat** : fond du scoreboard
    LIVE (enjeu par-dessus, semi-transparent) + slide « Affiche » du carousel
    (prochain match). Le carousel passe à **7 slides**. Contrat complet :
    [[affiche-match]].

## API de référence (cible)

Deux lectures publiques, décrites dans [[tv-state]] :
- `GET /api/tv/state/` — l'état **chaud** (hero packé `_pack_match`, enjeu,
  next, horloge), pollé ~2 s ;
- `GET /api/tv/idle/` — le contenu **froid** du carousel (slides), pollé
  ~10 s.

`GET /api/tv/upcoming/` et `GET /api/score_state/` sont absorbés/retirés.

## Hors périmètre

- **Second écran / multi-TV** : si un jour une seconde TV apparaît, les slides
  Poules/Tableau peuvent redevenir des routes dédiées — l'architecture en
  slides le permet, on ne le spécifie pas aujourd'hui.
- **Consultation mobile** : `/tv/live` reste un affichage 1080p ; un site
  public responsive est un autre chantier.
- **Sponsors / médias** (photos, logos) : non retenus au brainstorm.

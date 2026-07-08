---
sprint: 23
nom: "TV live : écran & retraits legacy"
specs:
  - specs/screens/tv-live.md
  - specs/tv-map.md
  - specs/technical/tv-state.md
modules:
  - frontend/app/src/stores/live.ts
  - frontend/app/src/types/index.ts
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/router/index.ts
  - live/views.py
  - live/urls.py
tickets-tag: sprint-23
branche: claude/sprint/23-tv-live-front
branche-parent: main
log: backlog/sprints/23-tv-live-front/log.md
---

# Sprint 23 — TV live : écran & retraits legacy

**Objectif :** Basculer l'écran `/tv/live` sur le contrat **tv-state** du
sprint 22 : scoreboard réparé avec **zone d'enjeu**, carousel réécrit
(**6 slides**, rotation par épreuve, annonces, bascule de journée), carte
**« Annonces TV »** côté admin — puis retirer **tout le legacy** (routes TV
dédiées, `score_state`, `tv/upcoming`, pages Django `results*`).

> Origine : audit TV + brainstorm produit du 2026-07-04. **Prérequis : le
> sprint 22** (endpoints `tv/state` + `tv/idle` + CRUD annonces) doit être
> terminé — le front bascule dessus, les retraits ne viennent qu'en dernier.
> Absorbe les issues historiques #3 (await manquant) et #21 (données figées),
> closes avec #259.

## Définition de terminé

- **Golden path LIVE :** démarrer un match de poule (arbitre ou admin) → la TV
  affiche le score complet (noms, sets, jeux, points, JEU DÉCISIF en
  tie-break) **et** le classement de la poule au centre, joueurs du match mis
  en évidence ; le bandeau « À suivre » annonce le next. Terminer le match →
  retour au carousel au poll suivant.
- **Golden path carousel :** sans match LIVE, rotation ~8 s sur les slides qui
  ont du contenu (les vides sont sautées, pager cohérent) ; les poules et le
  tableau tournent **par épreuve** ; un résultat saisi apparaît dans
  « Derniers résultats » (ordre `finished_at` desc) au poll idle suivant.
- **Golden path annonces :** créer une annonce depuis la carte « Annonces TV »
  (écran Tournoi) → elle apparaît sur la slide Annonces ; la désactiver → la
  slide la retire (ou est sautée).
- **Golden path programme :** journée courante épuisée → « Programme de
  demain » ; plus aucune journée → « Programme terminé ».
- **Retraits :** `/tv/groups` et `/tv/bracket` → redirection `/tv/live` ;
  `/results/…` → 404 ; `GET /api/score_state/` et `GET /api/tv/upcoming/`
  retirés ; `npx vue-tsc --noEmit` et `manage.py check` propres.
- Spec review `✅ Conforme` sur `tv-live.md` et `tv-state.md` (retraits
  compris).
- Aucune issue `sprint-23` ouverte (hors `en-attente`) — #3 et #21 closes.

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) — les deux états de l'écran, slides, cadences
- [`specs/tv-map.md`](../../../specs/tv-map.md) — décisions 1-2 (route unique, retrait legacy)
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) — § Front et § Retraits

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 23 — TV live : écran & retraits legacy »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#257](https://github.com/sirius911/moutilloux/issues/257) | live.ts + types sur le contrat tv-state | `stores/live.ts`, `types/index.ts` | `infra` — socle, orchestrateur |
| [#258](https://github.com/sirius911/moutilloux/issues/258) | TvScoreboard rebranché + zone d'enjeu | `TvScoreboard.vue` | Dépend de #257 |
| [#259](https://github.com/sirius911/moutilloux/issues/259) | TvIdle — carousel 6 slides sur tv/idle | `TvIdle.vue` | Dépend de #257 ; **ferme #3 et #21** |
| [#3](https://github.com/sirius911/moutilloux/issues/3) | TvIdle : await manquant (016, historique) | `TvIdle.vue` | Absorbée par #259 — close ensemble |
| [#261](https://github.com/sirius911/moutilloux/issues/261) | Retrait routes /tv/groups + /tv/bracket + SFC | `router/index.ts`, `TvPoules.vue`, `TvBracket.vue` | `infra` (router) ; après #259 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#260](https://github.com/sirius911/moutilloux/issues/260) | Carte « Annonces TV » (écran Tournoi) | `AdminTournoi.vue`, `admin-tournoi.md` | Dépend du CRUD sprint 22 (#256) |
| [#21](https://github.com/sirius911/moutilloux/issues/21) | TvIdle : données figées (029, historique) | `TvIdle.vue` | Absorbée par #259 — close ensemble |
| [#262](https://github.com/sirius911/moutilloux/issues/262) | Retraits back : score_state, tv/upcoming, results* | `views.py`, `urls.py`, templates | `infra` (urls) ; **dernier** ticket |

---

## Périmètre backend

- **#262 uniquement** (retraits) : retirer les routes `score_state`,
  `tv/upcoming` et `results*` de `urls.py`, supprimer les vues (`score_state`,
  `get_next_match`, `results*`) et les templates `results*` — **conserver**
  `get_hero_match` et `build_event_group_tables` (réutilisés par l'API).
  À faire strictement **après** #257/#258/#259 (le front ne doit plus rien
  consommer du legacy).

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/stores/live.ts` + `types/index.ts` — #257 (socle).
- `frontend/app/src/router/index.ts` — #261.
- `live/urls.py` — #262.
- **Contention** : `TvIdle.vue` touché par #259 (et cité par #3/#21 — même
  geste) ; `TvScoreboard.vue` par #258 seul. #258 ∥ #259 possibles (fichiers
  disjoints) une fois #257 livré.

## Ordre d'exécution suggéré

1. **#257** — le socle store/types (orchestrateur).
2. **#258** ∥ **#259** — les deux écrans en parallèle (fichiers disjoints).
   #259 clôt #3 et #21 dans la foulée.
3. **#260** — carte Annonces TV (indépendant des écrans TV, peut se faire en
   parallèle dès que le CRUD sprint 22 est là).
4. **#261** — retrait des routes/SFC front (après #259).
5. **#262** — retraits back, en dernier (plus aucun consommateur legacy).

**Parallélisme :** #257 d'abord ; puis (#258 ∥ #259 ∥ #260) ; puis #261 → #262
séquentiels.

---
sprint: 22
nom: "État TV : contrat back"
specs:
  - specs/technical/tv-state.md
modules:
  - live/api_views.py
  - live/views.py
  - live/models.py
  - live/admin_views.py
  - live/urls.py
tickets-tag: sprint-22
branche: claude/sprint/22-tv-state-back
branche-parent: main
log: backlog/sprints/22-tv-state-back/log.md
---

# Sprint 22 — État TV : contrat back

**Objectif :** Construire le **contrat de données TV** de
`specs/technical/tv-state.md` : deux endpoints publics sur `_pack_match`
(`/api/tv/state/` chaud, `/api/tv/idle/` froid), **une seule définition du
next**, et le modèle **Announcement** avec son CRUD. Le front ne bouge pas
dans ce sprint (il reste sur les endpoints actuels) — il bascule au sprint 23.

> Origine : audit TV + brainstorm produit du 2026-07-04 (specs `tv-map`,
> `tv-live`, `tv-state`). Contexte : le scoreboard SPA vit sur
> `GET /api/score_state/` (format snake_case pré-SPA) — le match LIVE ne
> s'affiche pas correctement et le `next` du store est écrasé par deux formes
> incompatibles. Ce sprint pose le **nouveau contrat en parallèle du legacy**
> (aucun retrait ici : les retraits sont au sprint 23, après bascule du front).

## Définition de terminé

- **Golden path état chaud :** un match LIVE → `GET /api/tv/state/` renvoie
  `hero` au format `_pack_match` complet (setScores, sideA/sideB objets,
  formatLabel), `stake.kind="group"` avec les standings de sa poule (les deux
  `entryId` du match présents) ; pour un match de tableau, `stake.kind="bracket"`.
  Aucun match LIVE → `hero: null`.
- **Golden path next :** matchs ordonnés uniquement demain → `next` = le
  premier de demain ; un match `order_index NULL` n'est jamais `next` ; le
  `next` de `tv/state` et celui du `programme` de `tv/idle` sont identiques.
- **Golden path idle :** `GET /api/tv/idle/` renvoie stats, les 5 derniers
  `FINISHED` par `finished_at` décroissant, les épreuves avec leurs
  poules/bracket, `programme.day` qui bascule `today → tomorrow → finished`,
  et les annonces actives.
- **Golden path annonces :** créer/éditer/désactiver/supprimer une annonce via
  les endpoints CRUD (superuser) ; `tv/idle` ne renvoie que les actives.
- Les deux endpoints sont **publics** (pas d'auth) et ne consomment aucun
  packer admin coûteux (`_pack_edition` interdit ici).
- Spec review `✅ Conforme` sur `specs/technical/tv-state.md` (sections
  contrat ; les retraits legacy restent ⚠ jusqu'au sprint 23 — attendu).
- Aucune issue `sprint-22` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) — contrat des deux endpoints, next unifié, modèle Announcement
- Référencées : [`specs/tv-map.md`](../../../specs/tv-map.md) (décisions), [`specs/technical/planning.md`](../../../specs/technical/planning.md) (définition du next)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 22 — État TV : contrat back »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#252](https://github.com/sirius911/moutilloux/issues/252) | Définition unique du « next » TV (journée courante) | `api_views.py` | Socle — débloque #253/#254 |
| [#255](https://github.com/sirius911/moutilloux/issues/255) | Modèle Announcement + migration | `models.py` | Socle — débloque #256, et #254 (clé announcements) |
| [#253](https://github.com/sirius911/moutilloux/issues/253) | `GET /api/tv/state/` (hero + stake + next) | `api_views.py`, `urls.py` | `infra` (route) ; dépend de #252 |
| [#254](https://github.com/sirius911/moutilloux/issues/254) | `GET /api/tv/idle/` (contenu du carousel) | `api_views.py`, `urls.py` | `infra` (route) ; dépend de #252 et #255 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#256](https://github.com/sirius911/moutilloux/issues/256) | CRUD Announcement (services + endpoints) | `admin_views.py`, `api_views.py`, `urls.py` | `infra` (routes) ; dépend de #255 |

---

## Périmètre backend

- **#252** — `get_tv_next(edition)` : première `PlayDay` ≥ aujourd'hui ayant
  des `SCHEDULED` ordonnés → plus petit `order_index` ; sinon `None`. Un seul
  endroit, consommé par #253 et #254.
- **#253** — packer d'état : `hero` (`get_hero_match` réutilisé), `stake`
  dérivé du hero (standings de sa poule via `GroupStanding`, ou
  `_pack_event_bracket` de son épreuve).
- **#254** — packer idle : agrégats simples (counts), `finished_at desc`,
  épreuves → groups/bracket, programme avec bascule de journée, annonces
  actives.
- **#255/#256** — modèle + CRUD conventionnel (services → endpoints fins).
- **Ne rien retirer** : `score_state`, `tv/upcoming`, `results*` restent en
  place jusqu'au sprint 23.

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` — 3 câblages (routes tv/state, tv/idle, CRUD annonces) :
  #253, #254, #256.
- `live/api_views.py` — touché par #252, #253, #254, #256 : blocs distincts
  (zone TV à créer en fin de fichier) mais fichier commun → séquencer.

## Ordre d'exécution suggéré

1. **#252** ∥ **#255** — les deux socles (fichiers disjoints).
2. **#253** — état chaud (dépend de #252).
3. **#254** — état froid (dépend de #252 + #255).
4. **#256** — CRUD annonces (dépend de #255), en parallèle de #253/#254 si
   agents distincts sur des blocs distincts, sinon en dernier.

**Parallélisme :** #252 ∥ #255 ; ensuite séquentiel sur `api_views.py`
(#253 → #254 → #256) sauf orchestration fine.

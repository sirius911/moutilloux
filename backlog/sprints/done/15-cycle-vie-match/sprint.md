---
sprint: 15
nom: "Cycle de vie d'un match : order_index persistant & Annulés"
specs:
  - specs/technical/planning.md
  - specs/screens/admin-matchs.md
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - live/models.py
  - live/referee_views.py
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/stores/event.ts
  - frontend/app/src/types/index.ts
tickets-tag: sprint-15
branche: claude/sprint/15-cycle-vie-match
branche-parent: main
log: backlog/sprints/15-cycle-vie-match/log.md
---

# Sprint 15 — Cycle de vie d'un match : order_index persistant & Annulés

**Objectif :** Faire qu'un match **garde sa place** dans le calendrier de bout en
bout. Aujourd'hui chaque transition de statut efface `order_index`, si bien qu'un
match **disparaît du calendrier** dès qu'il est lancé (et n'y revient jamais une
fois terminé). On rend `order_index` **persistant** à travers `LIVE`/`FINISHED`
(match visible + verrouillé à sa place), on bascule les `CANCELED` dans une
**colonne « Annulés »**, on corrige le moteur d'ETA, et on retire le flux kanban
legacy dangereux.

> Origine : analyse du cycle de vie d'un match (specs `planning` + `admin-matchs` +
> `cycle-de-vie-epreuve`, mises à jour en amont de ce sprint). Le **statut** décide
> désormais « déplaçable » (`SCHEDULED`) vs « verrouillé » (`LIVE`/`FINISHED`) ;
> `order_index = NULL` signifie **uniquement** « hors séquence » (jamais placé, ou
> annulé).

## Définition de terminé

- **Golden path déroulé :** lancer un match → il reste **visible et verrouillé**
  (« En cours ») à sa place dans la journée ; le terminer → il reste affiché
  (« Terminé », heure réelle) ; les heures aval se recalent sur la réalité. **Aucun
  match `LIVE`/`FINISHED` ne disparaît du calendrier.**
- **Golden path annulation :** annuler un match planifié → il **quitte sa journée**
  et apparaît dans la **colonne « Annulés »** (masquée s'il n'y en a aucun) ; la
  journée **récupère le créneau** (ETA recalée).
- **Golden path forfait :** un forfait reste **à sa place** (verrouillé, libellé
  « Forfait »), il ne disparaît pas.
- Endpoint legacy `POST /api/events/<id>/matches/reorder/` **supprimé** ; le drag
  du calendrier (`calendar/reorder/`) inchangé.
- Spec review `✅ Conforme` sur `specs/technical/planning.md` et
  `specs/screens/admin-matchs.md`.
- Aucune issue `sprint-15` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/technical/planning.md`](../../../specs/technical/planning.md) — invariant `order_index`, états dérivés, ETA/re-flow, retrait endpoint
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — colonne « Annulés », lignes verrouillées, statut
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) — forfait reste à sa place

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 15 — Cycle de vie d'un match : order_index persistant & Annulés »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#159](https://github.com/sirius911/moutilloux/issues/159) | Back : les transitions de statut n'effacent plus `order_index` | `models.py`, `referee_views.py`, `admin_views.py` | Socle : débloque le verrou + l'ETA front |
| [#160](https://github.com/sirius911/moutilloux/issues/160) | Back : CANCELED quitte la journée + bucket calendrier « Annulés » | `admin_views.py`, `api_views.py` | Débloque #164 |
| [#161](https://github.com/sirius911/moutilloux/issues/161) | Back : `reorder_calendar` fige LIVE comme FINISHED | `admin_views.py` | Rang LIVE non recalculé |
| [#162](https://github.com/sirius911/moutilloux/issues/162) | Retrait du flux kanban legacy `reorder_event_matches` (footgun) | `admin_views.py`, `api_views.py`, `urls.py`, `event.ts` | ⚠️ `urls.py` + `event.ts` = orchestrateur |
| [#163](https://github.com/sirius911/moutilloux/issues/163) | Front : verrouiller LIVE & FINISHED à leur place | `AdminMatches.vue` | Dépend de #159 |
| [#164](https://github.com/sirius911/moutilloux/issues/164) | Front : colonne « Annulés » conditionnelle (lecture seule) | `AdminMatches.vue`, `event.ts`, `types/index.ts` | Dépend de #160 |
| [#165](https://github.com/sirius911/moutilloux/issues/165) | Front : moteur ETA — ancrage réalité + « jamais d'avance surprise » | `AdminMatches.vue` | Dépend de #159 (+#160) |

### 🟡 Mineures

_Aucune._

---

## Périmètre backend

- **#159** — retirer les `order_index = None` de `mark_live`, des actions arbitre
  (start / finish / fin auto sur score), de `finalize_match_edit`→FINISHED, de
  `feature_match` et du forfait ; ajuster les `update_fields`. **Aucune migration.**
- **#160** — `finalize_match_edit` : `CANCELED` → `order_index`/`scheduled_time` à
  NULL ; `api_edition_calendar` renvoie une clé `canceled`.
- **#161** — `reorder_calendar` : `movable_statuses = [SCHEDULED]` seul.
- **#162** — suppression du service + de la vue + de la route legacy.

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` — suppression de la route `matches/reorder/` (#162).
- `frontend/app/src/stores/event.ts` — suppression de `reorderMatches` (#162) et
  extension du type `CalendarData` avec `canceled` (#164).
- **Contention** : `live/admin_views.py` est touché par #159, #160, #161, #162
  (dont `finalize_match_edit` par #159 **et** #160) → séquentiel, merge par
  l'orchestrateur. `AdminMatches.vue` est touché par #163, #164, #165 → séquentiel.

## Ordre d'exécution suggéré

1. **#159** — socle back (order_index persistant). Priorité : il rend visibles les
   LIVE/FINISHED et rend enfin utile le code front existant.
2. **#160** — CANCELED (même fichier `finalize_match_edit` que #159 → après #159).
3. **#161** — `reorder_calendar` (petit, `admin_views.py`).
4. **#162** — retrait legacy (infra : `urls.py`, `event.ts`).
5. **#163** — verrou front (dépend de #159).
6. **#164** — colonne « Annulés » (dépend de #160).
7. **#165** — ETA (dépend de #159, idéalement après #160).

**Parallélisme :** back (#159→#160, #161, #162) ∥ front une fois le socle back
livré. Les trois tickets front partagent `AdminMatches.vue` → à séquencer entre eux.

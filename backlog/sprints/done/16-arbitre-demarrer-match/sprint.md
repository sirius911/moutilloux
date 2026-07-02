---
sprint: 16
nom: "Arbitre : démarrer & lire un match"
specs:
  - specs/screens/arbitre-match.md
  - specs/screens/arbitre-home.md
  - specs/technical/cycle-de-vie-match.md
modules:
  - live/referee_views.py
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/composables/usePolling.ts
tickets-tag: sprint-16
branche: claude/sprint/16-arbitre-demarrer-match
branche-parent: main
log: backlog/sprints/16-arbitre-demarrer-match/log.md
---

# Sprint 16 — Arbitre : démarrer & lire un match

**Objectif :** Combler le **trou fonctionnel** de l'arbitrage : aujourd'hui la SPA
arbitre **n'appelle jamais** `start`, si bien qu'un match scoré **reste `SCHEDULED`
et n'apparaît jamais sur la TV**. On expose `démarrer` en **service partagé
(arbitre + admin)**, on donne à l'écran de saisie ses **trois états** (Démarrer /
LIVE / FINISHED lecture seule), on rend le **format lisible**, et on durcit
l'endpoint de liste.

> Origine : analyse de la partie arbitre et rédaction des specs `arbitre-home`,
> `arbitre-match` et `cycle-de-vie-match` (2026-07-01). Premier des deux sprints
> arbitre ; les **corrections & fins spéciales** (end_reason, forfait, abandon,
> tiroir Corrections, reopen) sont **réservées au Sprint 17**.
>
> S'appuie sur le **Sprint 15** : #159 (order_index persistant, y compris les
> actions arbitre) et #160 (CANCELED) sont un **prérequis** — non redupliqués ici.

## Définition de terminé

- **Golden path démarrage :** ouvrir un match PRÉVU (tablette **ou** admin) →
  « Démarrer » → le match passe `LIVE`, s'affiche sur la **TV**, garde sa place au
  calendrier ; scorer → fin **auto** sur la balle de match. Re-démarrer un match
  déjà `LIVE` = **no-op**.
- **Golden path invariant :** démarrer un second match rétrograde le précédent en
  `SCHEDULED` (score conservé) — un seul `LIVE` par édition.
- **Golden path lecture seule :** un match `FINISHED` n'offre **aucune action
  destructive** côté arbitre (Reset désactivé ; ré-ouverture = admin).
- **Format lisible :** l'en-tête de l'écran de saisie affiche le format
  (« 1 set à 5 · TB à 4 »).
- **Sécurité :** `GET /api/arbitre/matches/` refuse un compte sans rôle arbitre.
- Spec review `✅ Conforme` sur `specs/screens/arbitre-match.md` et
  `specs/screens/arbitre-home.md`.
- Aucune issue `sprint-16` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — états du match, en-tête (format), zones de tap
- [`specs/screens/arbitre-home.md`](../../../specs/screens/arbitre-home.md) — auth de la file, CTA
- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — transition Démarrer, service partagé, invariant mono-LIVE

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 16 — Arbitre : démarrer & lire un match »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#170](https://github.com/sirius911/moutilloux/issues/170) | Back : `démarrer` en service partagé (arbitre + admin), idempotent | `referee_views.py`, `admin_views.py`, `urls.py`, `api_views.py` | Socle ; ⚠️ `urls.py` = orchestrateur (`infra`) |
| [#171](https://github.com/sirius911/moutilloux/issues/171) | Front : ArbitreMatch — états du match (Démarrer / LIVE / FINISHED lecture seule) | `ArbitreMatch.vue` | Dépend de #170 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#172](https://github.com/sirius911/moutilloux/issues/172) | Back : `formatLabel` dans `_pack_match` | `api_views.py` | Débloque #173 |
| [#173](https://github.com/sirius911/moutilloux/issues/173) | Front : affichage du format dans l'en-tête arbitre | `ArbitreMatch.vue` | Dépend de #172 |
| [#174](https://github.com/sirius911/moutilloux/issues/174) | Back : `@referee_required` sur `GET /api/arbitre/matches/` | `api_views.py` | Indépendant |
| [#6](https://github.com/sirius911/moutilloux/issues/6) | usePolling : pause sur onglet caché (transverse) | `composables/usePolling.ts` | Existant, `infra` ; bénéficie à tous les écrans |

---

## Périmètre backend

- **#170** — extraire `start_match(match)` (service) réutilisé par
  `referee_action('start')` **et** un endpoint admin ; **idempotent** (déjà `LIVE`
  → no-op) ; conserver `mark_live` (invariant mono-`LIVE`) et `is_featured` ; **ne
  pas** ré-effacer `order_index` (traité par #159). Route admin dans `urls.py`
  (orchestrateur).
- **#172** — ajouter `formatLabel` (libellé dérivé du preset) dans `_pack_match`.
- **#174** — décorer `api_arbitre_matches` de `@referee_required`.

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` — nouvelle route `start` admin (#170).
- `frontend/app/src/composables/usePolling.ts` — pause onglet caché (#6, `infra`) ;
  bénéficie aussi à l'admin et à la TV.
- **Contention** : `ArbitreMatch.vue` est touché par #171 et #173 → séquentiel
  (#171 d'abord, #173 ensuite). `api_views.py` par #172 et #174 (blocs disjoints).

## Ordre d'exécution suggéré

1. **#170** — socle back (service `démarrer` partagé + idempotence). Débloque le
   front et la régie admin.
2. **#172** — `formatLabel` (petit, `api_views.py`), en parallèle de #170.
3. **#174** — `@referee_required` (une ligne), en parallèle.
4. **#171** — états du match front (dépend de #170) : le cœur du sprint.
5. **#173** — affichage format (dépend de #172, après #171 sur `ArbitreMatch.vue`).
6. **#6** — pause polling (transverse, indépendant, quand l'orchestrateur veut).

**Parallélisme :** back (#170 ∥ #172 ∥ #174) ∥ rien côté front tant que #170 n'est
pas livré. Les deux tickets front partagent `ArbitreMatch.vue` → séquentiels.

**Hors périmètre (Sprint 17) :** `end_reason`, forfait/abandon/annulation depuis la
tablette, tiroir « Corrections » (jeux±/sets±/serveur/swap), modal Terminer enrichi,
`reopen` non destructeur (admin).

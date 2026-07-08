---
sprint: 12
nom: Forfait & ajustements en cours de jeu
specs:
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - competition/models.py
  - live/models.py
  - live/admin_views.py
  - live/bracket.py
  - live/api_views.py
  - live/urls.py
  - frontend/app/src/stores/event.ts
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/views/admin/AdminMatches.vue
tickets-tag: sprint-12
branche: claude/sprint/12-forfait-ajustements
branche-parent: claude/sprint/11-cycle-de-vie-statut
log: backlog/sprints/12-forfait-ajustements/log.md
---

# Sprint 12 — Forfait & ajustements en cours de jeu

**Objectif :** Les quatre **ajustements ponctuels** possibles une fois l'épreuve
débutée (`EN_COURS`) : **remplacer** un joueur, déclarer un **forfait** (walkover),
**ajouter** un inscrit tardif, **retirer** un joueur (forfait en cascade).
Introduit la notion neuve de **walkover** (aujourd'hui un abandon = `CANCELED` sans
vainqueur). Dépend du statut posé au Sprint 11.

## Définition de terminé

- `Entry.withdrawn` + `Match.is_walkover` en base (migration OK)
- Services forfait / ajout tardif / remplacement exposés en `/api/`
- **Golden path :** déclarer un forfait → matchs à venir en walkover (vainqueur
  adverse), classements + tableau recalculés ; ajouter un tardif → ses matchs
  apparaissent « à planifier » ; remplacer un joueur → résultats conservés
- Spec review sur `specs/technical/cycle-de-vie-epreuve.md` (volet ajustements)
  → verdict `✅ Conforme`
- Aucun ticket `sprint-12` ouvert dans GitHub Issues (hors `en-attente`)

## Specs ciblées

- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md)
  → § Ajustements en phase de jeu (forfait / walkover)
- Écrans impactés : [[admin-poules]], [[admin-inscriptions]], [[admin-matchs]]

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 12 — Forfait & ajustements en cours de jeu »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#130](https://github.com/sirius911/moutilloux/issues/130) | Modèle `Entry.withdrawn` + `Match.is_walkover` + migration | `competition/models.py`, `live/models.py` | ⚠️ Infra — orchestrateur |
| [#131](https://github.com/sirius911/moutilloux/issues/131) | Service forfait (cascade walkover + recalcul + avance tableau) | `admin_views.py`, `bracket.py` | ⚠️ Infra — orchestrateur. Dépend de #130 |
| [#134](https://github.com/sirius911/moutilloux/issues/134) | Endpoints forfait / ajout tardif / remplacement | `api_views.py`, `urls.py` | ⚠️ Infra — orchestrateur. Dépend de #131, #132, #133 |
| [#136](https://github.com/sirius911/moutilloux/issues/136) | AdminGroups : affordances ajustements (forfait, remplacer, retirer, ajouter) | `AdminGroups.vue` | Dépend de #135 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#132](https://github.com/sirius911/moutilloux/issues/132) | Service ajout tardif (déverrouillage ciblé + re-génération additive) | `admin_views.py` | Dépend de S11 (#122, #124) |
| [#133](https://github.com/sirius911/moutilloux/issues/133) | Service remplacement (swap player/team, résultats conservés) | `admin_views.py` | — |
| [#135](https://github.com/sirius911/moutilloux/issues/135) | Store : actions `withdrawEntry` / `addLateEntry` / `replacePlayer` | `stores/event.ts` | ⚠️ Infra — orchestrateur. Dépend de #134 |
| [#137](https://github.com/sirius911/moutilloux/issues/137) | AdminInscriptions : chemin forfait + AdminMatches : badge walkover | `AdminInscriptions.vue`, `AdminMatches.vue` | Dépend de #135 |

---

## Périmètre backend

**Logique métier neuve** : le forfait/walkover n'existe nulle part aujourd'hui
(c'est un résultat avec vainqueur + cascade + recalcul). L'ajout tardif réutilise la
génération additive existante. `live/urls.py` câblé par l'orchestrateur.

## Ordre d'exécution suggéré

1. **#130 [infra]** — Modèle (champs walkover/withdrawn).
2. **#131 [infra]** — Service forfait (cascade + recalcul + tableau).
3. **#132 / #133** — Services ajout tardif & remplacement. Disjoints, parallélisables.
4. **#134 [infra]** — Endpoints + `urls.py`.
5. **#135 [infra]** — Store.
6. **#136 / #137** — Front, fichiers disjoints → parallélisables.

**Parallélisme :** #132 et #133 en parallèle après #130 ; #136 et #137 en parallèle
après #135.

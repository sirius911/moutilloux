---
sprint: 21
nom: "Durcissements API & specs"
specs:
  - specs/screens/admin-tournoi.md
  - specs/technical/planning.md
  - specs/technical/cycle-de-vie-epreuve.md
  - specs/technical/cycle-de-vie-match.md
modules:
  - live/admin_views.py
  - live/api_views.py
  - frontend/app/src/components/modals/EditionModal.vue
  - specs/
tickets-tag: sprint-21
branche: claude/sprint/21-durcissements-api-specs
branche-parent: main
log: backlog/sprints/21-durcissements-api-specs/log.md
---

# Sprint 21 — Durcissements API & specs

**Objectif :** Remonter côté **serveur** les règles métier qui vivent au mauvais
étage (activation de la première édition, auth du registre), **retirer** les
capacités API que les décisions produit ont rendues obsolètes (saisie d'heure,
court libre), et **réconcilier** les specs avec la réalité (marqueurs « à créer »
périmés, règles de classement jamais écrites, impasse de suppression de journée).

> Origine : audit externe specs ↔ code admin (2026-07-02). Volet « règles
> émergentes du code non écrites dans les specs » de l'audit : chaque issue
> tranche entre écrire la règle ou corriger le code.

## Définition de terminé

- **Golden path activation :** `POST /api/editions/create/` sans édition active
  → l'édition créée est active (règle serveur, plus de paramètre `activate`).
- **Golden path auth :** un compte arbitre ne peut ni lister ni créer de fiches
  du registre ; la matrice d'accès (public / arbitre / superuser) est écrite.
- **Golden path API :** `matches/<id>/edit/` ignore `scheduled_time`/`court` ;
  un nom de court inconnu → 400 (aucune création à la volée).
- `specs/technical/classement-poule.md` existe ; les tableaux « ce qui est
  neuf » des cycles de vie reflètent l'état réel ; l'impasse `delete_play_day`
  est tranchée et écrite ; la durée par défaut se règle depuis la modale Édition.
- Aucune issue `sprint-21` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md) — modale Édition (#211, #216)
- [`specs/technical/planning.md`](../../../specs/technical/planning.md) — journées, durée (#215, #216)
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) / [`cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — réconciliation (#218)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 21 — Durcissements API & specs »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#211](https://github.com/sirius911/moutilloux/issues/211) | Activation auto de la première édition côté front seulement | `admin_views.py`, `EditionModal.vue` | Règle → serveur |
| [#212](https://github.com/sirius911/moutilloux/issues/212) | Auth du registre incohérente + matrice d'accès non documentée | `api_views.py`, `specs/` | `infra` |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#213](https://github.com/sirius911/moutilloux/issues/213) | _resolve_court_pk crée des courts à la volée | `api_views.py` | Avec #214 (même zone) |
| [#214](https://github.com/sirius911/moutilloux/issues/214) | MatchEditForm accepte encore scheduled_time et court | `admin_views.py`, `api_views.py` | Décisions 18-19 |
| [#215](https://github.com/sirius911/moutilloux/issues/215) | Journée avec matchs terminés insupprimable — impasse à trancher | `admin_views.py`, `specs/` | Décision produit d'abord |
| [#216](https://github.com/sirius911/moutilloux/issues/216) | Durée de match par défaut sans UI (modale Édition) | `EditionModal.vue` | |
| [#217](https://github.com/sirius911/moutilloux/issues/217) | Specs : règles de classement de poule à écrire | `specs/technical/`, `standings.py` | Spec d'abord, code si écart |
| [#218](https://github.com/sirius911/moutilloux/issues/218) | Specs : marqueurs « à créer » périmés (cycle-de-vie-*) | `specs/technical/` | Lecture seule code |
| [#219](https://github.com/sirius911/moutilloux/issues/219) | Vues panel_* legacy : trancher le retrait | `admin_views.py`, `admin_urls.py`, templates | Décision produit d'abord |

---

## Périmètre backend

- **#211** — `create_edition` : auto-activation si aucune édition active ;
  retirer `activate` du contrat.
- **#212** — `@superuser_required` sur `api_players` / `api_player_create`
  (vérifier qu'aucun écran arbitre ne les consomme) + spec matrice d'accès.
- **#213/#214** — durcir `api_match_edit` : plus de `scheduled_time`/`court`
  éditables, plus de `get_or_create` de court.
- **#215/#219** — décisions à trancher (dans l'issue) avant d'écrire le code.

## Fichiers partagés (orchestrateur uniquement)

- `live/api_views.py` et `live/admin_views.py` — touchés par #211, #212, #213,
  #214, #215, #219 : séquencer, blocs distincts mais fichiers communs.
- `specs/` — #212, #215, #217, #218 écrivent des specs : passer #218 en premier
  (réconciliation) pour que les autres écrivent sur une base à jour.

## Ordre d'exécution suggéré

1. **#218** — réconciliation des specs (rend la suite lisible).
2. **#211** ∥ **#212** — les deux majeures back (blocs disjoints).
3. **#213 + #214** — durcissement de l'édition de match (même zone, un geste).
4. **#217** — spec classement (+ correctif standings si écart retenu).
5. **#215** puis **#219** — décisions produit puis implémentation.
6. **#216** — UI durée par défaut (indépendant, à tout moment).

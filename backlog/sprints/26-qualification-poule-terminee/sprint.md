---
sprint: 26
nom: "Qualification à la poule terminée"
specs:
  - specs/technical/cycle-de-vie-epreuve.md
  - specs/technical/classement-poule.md
  - specs/screens/admin-tableau-final.md
  - specs/technical/tv-state.md
modules:
  - live/bracket.py
  - live/api_views.py
  - live/views.py
  - frontend/app/src/views/admin/AdminBracket.vue
tickets-tag: sprint-26
branche: claude/sprint/26-qualification-poule-terminee
branche-parent: main
log: backlog/sprints/26-qualification-poule-terminee/log.md
---

# Sprint 26 — Qualification à la poule terminée

**Objectif :** aligner la qualification sur la décision 30 (revue produit
2026-07-07) : une poule ne produit ses qualifiés (badge Q, placement dans le
tableau, panneau « Qualifiés disponibles ») que lorsque **tous ses matchs sont
joués** — jamais sur classement partiel. Grain **par poule** (on n'attend pas
les autres poules de l'épreuve).

> Origine : revue produit 2026-07-07 (« les joueurs qualifiés doivent être
> définis que lorsque les poules sont terminées », « à quoi sert le Q ? »).
> Le cœur est back : un helper « poule terminée » partagé entre `bracket.py`
> et les quatre calculs du flag `qualified`.

## Définition de terminé

- Golden path : dans une poule de 3+, terminer un seul match → aucun badge Q
  nulle part (admin Poules, TV), aucun slot du tableau rempli, panneau
  « Qualifiés disponibles » vide ; terminer le dernier match de la poule → Q,
  placements et panneau se remplissent au poll suivant.
- Spec review `✅ Conforme` sur [[cycle-de-vie-epreuve]] (§ « Poule terminée »)
  et [[admin-tableau-final]].
- Aucune issue `sprint-26` ouverte.

## Specs ciblées

- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) — définition « poule terminée », écart connu documenté
- [`specs/technical/classement-poule.md`](../../../specs/technical/classement-poule.md) — classement ≠ qualification
- [`specs/screens/admin-tableau-final.md`](../../../specs/screens/admin-tableau-final.md) — panneau Qualifiés, placement automatique
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) — flag `qualified` des standings

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 26 — Qualification à la poule terminée »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#289](https://github.com/sirius911/moutilloux/issues/289) | Back : bracket.py résout les qualifiés sur classement partiel — garde « poule terminée » | `live/bracket.py` | crée le helper partagé — **à faire en premier** |
| [#290](https://github.com/sirius911/moutilloux/issues/290) | Back : flag qualified vrai dès le classement partiel (4 calculs à garder) | `live/api_views.py`, `live/views.py` | dépend du helper de #289 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#291](https://github.com/sirius911/moutilloux/issues/291) | Front : AdminBracket — état vide « Aucune poule terminée » + qualification 100% serveur | `frontend/app/src/views/admin/AdminBracket.vue` | |

---

## Périmètre backend

Tout le cœur du sprint : helper `group_is_finished` + gardes dans `bracket.py`,
`api_views.py` (×3) et `views.py`. Aucune migration.

## Fichiers partagés (orchestrateur uniquement)

Aucun (`live/urls.py` non touché — pas de nouvelle route).

## Ordre d'exécution suggéré

1. #289 (helper + garde bracket) — débloque #290.
2. #290 (flag qualified ×4).
3. #291 (front, indépendant après #290 pour vérifier le rendu).

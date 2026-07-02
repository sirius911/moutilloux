---
sprint: 18
nom: "Tableau final conforme"
specs:
  - specs/screens/admin-tableau-final.md
modules:
  - frontend/app/src/views/admin/AdminBracket.vue
  - live/api_views.py
  - live/admin_views.py
  - live/bracket.py
tickets-tag: sprint-18
branche: claude/sprint/18-tableau-final-conformite
branche-parent: main
log: backlog/sprints/18-tableau-final-conformite/log.md
---

# Sprint 18 — Tableau final conforme

**Objectif :** Aligner l'écran Tableau final et l'API bracket sur
`admin-tableau-final.md` : la **petite finale (P3) devient ajustable** (labels,
assign, clear), la **recréation forcée fonctionne réellement**, et l'écran
retrouve le sélecteur d'épreuve, le polling et les conventions de modale.

> Origine : audit externe specs ↔ code admin (2026-07-02). Prérequis déjà en
> place : le squelette (3 poules, byes, P3) est posé par « Débuter » depuis le
> commit `c395cee` — ce sprint traite ce qui reste après ce correctif.

## Définition de terminé

- **Golden path P3 :** sur une épreuve avec petite finale, éditer les étiquettes
  du slot P3, y déposer un qualifié, vider une place → succès (plus de 404),
  mêmes règles que QF/SF/F (refus si match commencé).
- **Golden path recréation :** « Recréer le tableau » (modale, pas `confirm()`)
  → les matchs `SCHEDULED` du tableau sont reposés proprement ; refus (400)
  si un match du tableau est LIVE/FINISHED.
- **Golden path écran :** le sélecteur d'épreuve navigue (`:eventId`), la
  progression d'un gagnant saisie côté arbitre apparaît sans recharger
  (polling), et en `INSCRIPTION` l'écran invite à débuter (pas de bouton Créer).
- Spec review `✅ Conforme` sur `admin-tableau-final.md`.
- Aucune issue `sprint-18` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-tableau-final.md`](../../../specs/screens/admin-tableau-final.md) — en-tête, recréation, slots, qualifiés, progression

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 18 — Tableau final conforme »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#196](https://github.com/sirius911/moutilloux/issues/196) | Back : P3 exclue de bracket-labels / assign / clear (404) | `api_views.py`, `admin_views.py` | Socle P3 |
| [#197](https://github.com/sirius911/moutilloux/issues/197) | Back : api_bracket_create ignore start_stage/force | `api_views.py`, `bracket.py` | Redéfinit la sémantique de « Recréer » |
| [#195](https://github.com/sirius911/moutilloux/issues/195) | Front : sélecteur d'épreuve manquant en en-tête (décision 16) | `AdminBracket.vue` | Pattern des 3 autres écrans |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#198](https://github.com/sirius911/moutilloux/issues/198) | Front : AdminBracket sans polling | `AdminBracket.vue` | |
| [#199](https://github.com/sirius911/moutilloux/issues/199) | Front : recréation via confirm() natif → modale | `AdminBracket.vue` | Dépend de #197 (texte exact) |
| [#200](https://github.com/sirius911/moutilloux/issues/200) | Front : « Créer le tableau » proposé en INSCRIPTION | `AdminBracket.vue` | |
| [#176](https://github.com/sirius911/moutilloux/issues/176) | Back : stage_label de _pack_match ne couvre pas P3 | `api_views.py` | Issue existante réutilisée |

---

## Périmètre backend

- **#196** — inclure `Match.Stage.P3` dans `_final_matches_qs`,
  `api_bracket_labels` (et vérifier assign/clear).
- **#197** — service de recréation : supprimer les matchs `SCHEDULED` du
  tableau puis `live/bracket.ensure_final_bracket_exists` ; garde 400 si
  LIVE/FINISHED ; retirer le paramètre `start_stage` obsolète du contrat.
- **#176** — libellé « Petite finale » dans `stage_label`.

## Fichiers partagés (orchestrateur uniquement)

- `live/api_views.py` — touché par #196, #197, #176 (blocs proches du bloc
  bracket) : orchestrateur ou séquence stricte.
- **Contention front** : `AdminBracket.vue` touché par #195, #198, #199, #200 →
  séquentiel.

## Ordre d'exécution suggéré

1. **#196** ∥ **#176** — P3 côté API (petits, débloquent l'UI petite finale).
2. **#197** — recréation forcée (fixe la sémantique avant de toucher l'UI).
3. **#195** — sélecteur d'épreuve (premier chantier front).
4. **#198** → **#200** → **#199** — polling, état INSCRIPTION, modale de
   recréation (même fichier, séquentiel ; #199 en dernier car dépend de #197).

**Parallélisme :** back (#196 ∥ #176, puis #197) ∥ rien côté front avant #197.

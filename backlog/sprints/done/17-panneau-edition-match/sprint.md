---
sprint: 17
nom: "Panneau d'édition de match"
specs:
  - specs/screens/admin-matchs.md
  - specs/technical/cycle-de-vie-match.md
modules:
  - live/admin_views.py
  - live/api_views.py
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/views/admin/AdminMatches.vue
tickets-tag: sprint-17
branche: claude/sprint/17-panneau-edition-match
branche-parent: main
log: backlog/sprints/17-panneau-edition-match/log.md
---

# Sprint 17 — Panneau d'édition de match

**Objectif :** Rendre le panneau d'édition de match (volet latéral du Calendrier)
conforme à `admin-matchs.md` et `cycle-de-vie-match.md` : l'onglet Format
**enregistre réellement**, l'invariant **mono-LIVE** n'est plus contournable,
les transitions sensibles sont **confirmées**, et les décisions 5-6
(Historique, Abandon) sont appliquées.

> Origine : audit externe specs ↔ code admin (2026-07-02). Les 3 écarts majeurs
> de l'audit (générateur de tableau au Débuter, calendrier édition-entière,
> recalculs du chemin admin) sont **déjà corrigés** (commit `c395cee`) — non
> redupliqués ici.
>
> ⚠️ Le sprint 16 annonçait un « Sprint 17 » arbitre (fins spéciales :
> `end_reason`, forfait/abandon tablette, tiroir Corrections, reopen). Ce
> chantier-là **reste à planifier séparément** — il n'est pas ce sprint.

## Définition de terminé

- **Golden path Format :** panneau d'un match PRÉVU → onglet Format → changer le
  preset → Enregistrer → le format est persisté (visible dans `formatLabel`).
  Sur un match LIVE, les champs sont verrouillés **et** ignorés par le serveur.
- **Golden path mono-LIVE :** panneau → Statut « En direct » alors qu'un autre
  match est LIVE → confirmation, puis l'ancien LIVE repasse SCHEDULED (score
  conservé) et le nouveau est à l'antenne TV. Jamais deux LIVE simultanés.
- **Golden path garde :** Statut « Terminé » sans vainqueur → erreur 400
  affichée dans le pied du panneau, match inchangé.
- Plus d'onglet Historique, plus d'option Abandon, plus de `window.confirm`.
- Spec review `✅ Conforme` sur `admin-matchs.md` (§ Panneau d'édition) et
  `cycle-de-vie-match.md` (§ Démarrer, § Terminer).
- Aucune issue `sprint-17` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — panneau d'édition (onglets Score / Format / Planning, mise en avant)
- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — invariant mono-LIVE, garde de confirmation, FINISHED avec vainqueur

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 17 — Panneau d'édition de match »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#189](https://github.com/sirius911/moutilloux/issues/189) | Back : passage LIVE via le panneau contourne mark_live (invariant mono-LIVE) | `api_views.py`, `admin_views.py` | Socle ; `infra` (service mutualisé) |
| [#190](https://github.com/sirius911/moutilloux/issues/190) | Back : FINISHED sans vainqueur accepté (garde serveur manquante) | `admin_views.py` | Indépendant |
| [#191](https://github.com/sirius911/moutilloux/issues/191) | Front : Démarrer sans confirmation quand un autre match est LIVE | `AdminMatches.vue`, `EditMatchPanel.vue` | Dépend de #189 pour le panneau |
| [#7](https://github.com/sirius911/moutilloux/issues/7) | EditMatchPanel : onglet Format silencieusement ignoré à la sauvegarde | `EditMatchPanel.vue` | Issue historique (021) réutilisée |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#192](https://github.com/sirius911/moutilloux/issues/192) | EditMatchPanel : onglet « Historique » à supprimer (décision 5) | `EditMatchPanel.vue` | |
| [#168](https://github.com/sirius911/moutilloux/issues/168) | EditMatchPanel : option « Abandon » du sélecteur Vainqueur (décision 6) | `EditMatchPanel.vue` | Issue existante réutilisée |
| [#193](https://github.com/sirius911/moutilloux/issues/193) | EditMatchPanel : points du jeu en cours éditables mais jamais enregistrés | `EditMatchPanel.vue` | |
| [#194](https://github.com/sirius911/moutilloux/issues/194) | Mise en avant : ConfirmModal + désactivation possible | `EditMatchPanel.vue`, `admin_views.py` | |
| [#175](https://github.com/sirius911/moutilloux/issues/175) | Docstring api_match_feature obsolète (order_index=None) | `api_views.py` | Une ligne |

---

## Périmètre backend

- **#189** — `api_match_edit` / `finalize_match_edit` : un statut demandé `LIVE`
  passe par `start_match()` (mark_live + featured + rétrogradation), jamais par
  le form brut.
- **#190** — garde : `FINISHED` exige `winner_side` (400 sinon).
- **#194** — extinction de la mise en avant (`is_featured=False` sans changer le
  statut).

## Fichiers partagés (orchestrateur uniquement)

- `live/admin_views.py` (services mutualisés `start_match` / `finalize_match_edit`)
  — #189, #190, #194 : blocs proches, à traiter par l'orchestrateur ou en
  séquence stricte.
- **Contention front** : `EditMatchPanel.vue` est touché par #7, #191, #192,
  #193, #194 et #168 → **séquentiel** (un seul agent front à la fois sur ce
  fichier).

## Ordre d'exécution suggéré

1. **#189** — socle back mono-LIVE (débloque le comportement du panneau).
2. **#190** ∥ **#175** — petites gardes/doc back, en parallèle de #189 (blocs disjoints, à séquencer si même fichier).
3. **#7** — brancher l'onglet Format (le cœur du sprint côté front).
4. **#192** puis **#168** puis **#193** — nettoyages du panneau (même fichier, séquentiel).
5. **#194** — mise en avant (front + back extinction).
6. **#191** — confirmations Démarrer (AdminMatches + panneau), en dernier : dépend du comportement final de #189.

**Parallélisme :** back (#189 ∥ #190 ∥ #175) ; front strictement séquentiel sur
`EditMatchPanel.vue`.

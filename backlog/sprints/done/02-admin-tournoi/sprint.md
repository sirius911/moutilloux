---
sprint: 02
nom: Admin Tournoi
specs:
  - specs/screens/admin-tournoi.md
modules:
  - admin/tournoi
  - admin/modals
tickets-tag: sprint-02
branche: sprint/02-admin-tournoi
branche-parent: main
log: backlog/sprints/02-admin-tournoi/log.md
---

# Sprint 02 — Admin Tournoi

**Objectif :** Aligner `AdminTournoi.vue`, `EditionModal.vue` et `EventModal.vue`
sur la spec `admin-tournoi.md`. L'écran doit passer une spec-review conforme à
l'issue du sprint.

## Définition de terminé

- Spec review sur `specs/screens/admin-tournoi.md` → verdict `✅ Conforme`
- Aucun ticket `[sprint-02]` restant dans `backlog/backlog.md`

## Specs ciblées

- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md)
  → fichiers : `AdminTournoi.vue`, `EditionModal.vue`, `EventModal.vue`,
  `stores/event.ts`, `live/api_views.py`

---

## Tickets du sprint

### 🟠 Majeures

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [022](../../022-event-store-activeEventId-null-assertion.md) | event.ts : `activeEventId!` → URLs `/api/events/undefined/…` | `stores/event.ts` |
| [039](../../039-admin-tournoi-stats-epreuve-au-lieu-edition.md) | AdminTournoi : stats calculées sur l'épreuve active mais étiquetées « édition » | `AdminTournoi.vue`, `api_views.py` |
| [051](../../051-edition-modal-checkbox-activer-non-conforme.md) | EditionModal : case « Activer immédiatement » absente de la spec | `EditionModal.vue` |
| [052](../../052-event-modal-creation-categorie-inline-manquante.md) | EventModal : création de catégorie inline manquante | `EventModal.vue`, `api_views.py` |
| [053](../../053-admin-tournoi-carte-epreuve-incomplete.md) | AdminTournoi : carte épreuve incomplète (état, inscrits, libellé bouton) | `AdminTournoi.vue` |
| [054](../../054-admin-tournoi-carte-edition-active-incomplete.md) | AdminTournoi : carte édition active incomplète (état vide, dates, bloc méta fictif) | `AdminTournoi.vue` |

### 🟡 Mineures

| # | Titre | Fichier(s) |
|---|-------|-----------|
| [028](../../028-modal-shell-escape-absent.md) | ModalShell : fermeture sur Escape non implémentée | `ModalShell.vue` |
| [046](../../046-confirmations-destructives-window-confirm.md) | AdminTournoi : confirmations destructives via `window.confirm()` | `AdminTournoi.vue` |

> **Note ticket 007** : subsumé par le ticket 039 — les deux seront fermés
> ensemble quand les stats d'édition seront correctement exposées par l'API.

---

## Périmètre backend (connectique API)

Deux ajouts nécessaires côté `live/api_views.py` :

1. **Agrégats d'édition** dans `_pack_edition` :
   - `distinctPlayersCount` : joueurs distincts inscrits à au moins une épreuve
     de l'édition (les deux membres d'une équipe comptent chacun → `Entry` distinct
     player count sur l'édition).
   - `matchesFinished` / `matchesTotal` : matchs terminés / total, toutes épreuves
     de l'édition confondues.
   - Ces champs alimentent la carte « Édition active » sans requête supplémentaire
     côté front.

2. **Endpoint création catégorie** : vérifier si
   `POST /api/categories/create/` existe déjà ; sinon l'ajouter pour le ticket 052.

---

## Ordre d'exécution suggéré

```
022 (event.ts guard)          → fondation, débloquer en premier
039 + 054 (stats + carte)    → back + front en parallèle
053 (carte épreuve)           → front seul
051 (EditionModal checkbox)   → front seul
052 (inline category)         → back + front, le plus complexe
028 (Escape)                  → front seul, rapide
046 (ConfirmModal)            → front seul, crée ConfirmModal.vue
```

Le ticket 052 est le plus complexe (back + front). Il peut être mis en parallèle
avec le reste du sprint une fois le contrat API confirmé.

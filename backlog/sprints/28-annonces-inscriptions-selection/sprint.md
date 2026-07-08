---
sprint: 28
nom: "Admin : annonces & inscription par sélection"
specs:
  - specs/screens/admin-tournoi.md
  - specs/screens/admin-inscriptions.md
modules:
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
tickets-tag: sprint-28
branche: claude/sprint/28-annonces-inscriptions-selection
branche-parent: main
log: backlog/sprints/28-annonces-inscriptions-selection/log.md
---

# Sprint 28 — Admin : annonces & inscription par sélection

**Objectif :** deux retouches front indépendantes issues de la revue produit
2026-07-07 : édition inline du message d'annonce (décision 26 — l'endpoint
back existe déjà) et remplacement de « Inscrire les N affichés » par la
sélection par cases à cocher (décision 28).

> Sprint 100 % front, sans migration ni route nouvelle. Les deux tickets
> touchent des SFC distinctes → parallélisables.

## Définition de terminé

- Golden path annonces : modifier le message d'une annonce inline (Entrée
  valide, Échap annule, vide refusé) → la TV diffuse le nouveau texte.
- Golden path inscriptions : rechercher, « Tout cocher », élargir la recherche,
  cocher un joueur de plus → « Inscrire la sélection (N) » inscrit exactement
  les cochés ; la sélection se vide après réussite.
- Spec review `✅ Conforme` sur [[admin-tournoi]] (carte Annonces) et
  [[admin-inscriptions]].
- Aucune issue `sprint-28` ouverte.

## Specs ciblées

- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md) — carte « Annonces TV », action Modifier
- [`specs/screens/admin-inscriptions.md`](../../../specs/screens/admin-inscriptions.md) — sélection par cases à cocher

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 28 — Admin : annonces & inscription par sélection »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#298](https://github.com/sirius911/moutilloux/issues/298) | Front : AdminInscriptions — inscription par sélection (cases à cocher + Tout cocher) | `frontend/app/src/views/admin/AdminInscriptions.vue` | |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#297](https://github.com/sirius911/moutilloux/issues/297) | Front : AdminTournoi — édition inline du message d'annonce | `frontend/app/src/views/admin/AdminTournoi.vue` | endpoint back déjà en place |

---

## Périmètre backend

Aucun.

## Fichiers partagés (orchestrateur uniquement)

Aucun.

## Ordre d'exécution suggéré

#297 ∥ #298 (SFC distinctes, aucun couplage).

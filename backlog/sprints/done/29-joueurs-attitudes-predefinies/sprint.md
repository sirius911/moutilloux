---
sprint: 29
nom: "Joueurs : attitudes prédéfinies"
specs:
  - specs/screens/admin-joueurs.md
  - specs/technical/affiche-match.md
modules:
  - core/models.py
  - live/api_views.py
  - frontend/app/src/constants/attitudes.json
  - frontend/app/src/components/modals/AddPlayerModal.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/types/index.ts
tickets-tag: sprint-29
branche: claude/sprint/29-joueurs-attitudes-predefinies
branche-parent: main
log: backlog/sprints/29-joueurs-attitudes-predefinies/log.md
---

# Sprint 29 — Joueurs : attitudes prédéfinies

**Objectif :** décision 27 — les attitudes de mise en scène deviennent une
**multi-sélection** depuis une liste prédéfinie (`constants/attitudes.json`),
plus de texte libre ; la génération d'affiche **pioche au hasard** parmi les
attitudes du joueur, sauf choix explicite dans l'onglet Affiche.

> Origine : revue produit 2026-07-07. **Pas de migration de données**
> (décision explicite : aucune donnée de prod) — seulement la migration de
> schéma `attitude` (CharField) → `attitudes` (JSONField liste).

## Définition de terminé

- Golden path : fiche joueur → cocher 3 attitudes → enregistrer → rouvrir : les
  3 sont cochées ; onglet Affiche d'un match du joueur → le champ est pré-rempli
  par l'une des 3 (tirage) ; la remplacer par un choix explicite → la génération
  part avec ce choix.
- `npx vue-tsc --noEmit` passe (type `Player.attitudes: string[]`).
- Spec review `✅ Conforme` sur [[admin-joueurs]] et [[affiche-match]].
- Aucune issue `sprint-29` ouverte.

## Specs ciblées

- [`specs/screens/admin-joueurs.md`](../../../specs/screens/admin-joueurs.md) — champ Attitudes multi-sélection
- [`specs/technical/affiche-match.md`](../../../specs/technical/affiche-match.md) — `Player.attitudes`, tirage au sort au pré-remplissage

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 29 — Joueurs : attitudes prédéfinies »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#299](https://github.com/sirius911/moutilloux/issues/299) | Back : Player.attitude → Player.attitudes (liste JSON) + packers et endpoints | `core/models.py`, `live/api_views.py` | **à faire en premier** (contrat) |
| [#300](https://github.com/sirius911/moutilloux/issues/300) | Front : constants/attitudes.json + multi-sélection dans la fiche joueur | `frontend/app/src/constants/attitudes.json`, `AddPlayerModal.vue`, `types/index.ts` | dépend de #299 |
| [#301](https://github.com/sirius911/moutilloux/issues/301) | Front : onglet Affiche — tirage au sort + choix explicite d'attitude | `EditMatchPanel.vue` | dépend de #299 et #300 |

---

## Périmètre backend

Migration de schéma `Player.attitudes` (JSONField, défaut `[]`), endpoints
player create/edit, `_pack_entry`/`_pack_team`. Le serveur ne re-valide pas les
valeurs contre la liste (elle vit côté front).

## Fichiers partagés (orchestrateur uniquement)

`frontend/app/src/types/index.ts` (type `Player`) — modification ponctuelle,
coordonnée par l'orchestrateur si un autre agent travaille en parallèle.

## Ordre d'exécution suggéré

1. #299 (back : modèle + packers).
2. #300 (constants + fiche joueur).
3. #301 (onglet Affiche).
Séquentiel : #300 et #301 consomment le contrat de #299.

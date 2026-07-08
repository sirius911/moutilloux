---
sprint: 19
nom: "Poules & inscriptions : ajustements"
specs:
  - specs/screens/admin-poules.md
  - specs/screens/admin-inscriptions.md
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - live/admin_views.py
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/components/modals/AutoFillModal.vue
tickets-tag: sprint-19
branche: claude/sprint/19-poules-inscriptions-ajustements
branche-parent: main
log: backlog/sprints/19-poules-inscriptions-ajustements/log.md
---

# Sprint 19 — Poules & inscriptions : ajustements

**Objectif :** Aligner les écrans Poules et Inscriptions sur les specs : le
**retrait** d'un joueur en cours de jeu devient distinct du **forfait** (retrait
de l'affichage poule), le retrait sec est **gardé par le statut**, l'ajout
tardif suit la règle « dépassement possible, averti », et les finitions de
composition (lettre, nom d'équipe, défauts) sont corrigées.

> Origine : audit externe specs ↔ code admin (2026-07-02).

## Définition de terminé

- **Golden path retrait :** épreuve EN_COURS → « Retirer » un joueur → walkovers
  posés **et** le joueur disparaît de la carte de poule ; « Forfait » → walkovers
  posés, le joueur reste affiché barré (WO). Deux effets distincts.
- **Golden path garde :** retrait sec (`remove_entry`) refusé hors phase
  d'inscription avec message explicite.
- **Golden path ajout tardif :** ajouter un joueur dans une poule à l'effectif
  → accepté, avertissement « au-delà de l'effectif » affiché (overCapacity).
- Poules A et C existantes → « + Nouvelle poule » crée **B** ; en Double, les
  équipes s'affichent par leur nom ; AutoFill s'ouvre sur la taille de
  l'épreuve ; un ✕ refusé affiche le message serveur.
- Spec review `✅ Conforme` sur `admin-poules.md` et `admin-inscriptions.md`.
- Aucune issue `sprint-19` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-poules.md`](../../../specs/screens/admin-poules.md) — composition, verrouillage, ajustements
- [`specs/screens/admin-inscriptions.md`](../../../specs/screens/admin-inscriptions.md) — retrait d'une inscription
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) — forfait vs retrait, ajout tardif

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 19 — Poules & inscriptions : ajustements »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#201](https://github.com/sirius911/moutilloux/issues/201) | Back+Front : « Retirer » ≡ « Forfait » — pas de retrait de l'affichage poule | `admin_views.py`, `AdminGroups.vue` | Socle du sprint |
| [#166](https://github.com/sirius911/moutilloux/issues/166) | Back : remove_entry sans garde de statut d'épreuve | `admin_views.py` | Issue existante réutilisée |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#202](https://github.com/sirius911/moutilloux/issues/202) | Ajout tardif impossible au-delà de l'effectif, overCapacity ignoré | `AdminGroups.vue` | |
| [#203](https://github.com/sirius911/moutilloux/issues/203) | « + Nouvelle poule » : première lettre libre | `AdminGroups.vue` | |
| [#204](https://github.com/sirius911/moutilloux/issues/204) | « Équipe {id} » au lieu du nom d'équipe (Non assignés) | `AdminGroups.vue` | |
| [#205](https://github.com/sirius911/moutilloux/issues/205) | AutoFillModal : défaut = taille de poule de l'épreuve | `AutoFillModal.vue` | Indépendant |
| [#206](https://github.com/sirius911/moutilloux/issues/206) | ✕ de retrait de poule sans gestion d'erreur | `AdminGroups.vue` | |

---

## Périmètre backend

- **#201** — étendre `withdraw_entry` (ou service dédié) : option « retrait »
  = cascade walkover **puis** suppression du `GroupMembership` (standings
  recalculés). Exposer la distinction dans l'endpoint.
- **#166** — garde de statut sur `remove_entry` (retrait sec réservé à
  `INSCRIPTION` ; message renvoyant vers le forfait/retrait en jeu).

## Fichiers partagés (orchestrateur uniquement)

- `live/admin_views.py` — services mutualisés (`withdraw_entry`, `remove_entry`)
  touchés par #201 et #166 : orchestrateur ou séquence stricte.
- **Contention front** : `AdminGroups.vue` touché par #201, #202, #203, #204,
  #206 → séquentiel. `AdminInscriptions.vue` touché par #201 (libellés
  Retirer/Forfait) après le back.

## Ordre d'exécution suggéré

1. **#166** — garde `remove_entry` (petit, indépendant).
2. **#201 back** — service retrait vs forfait (fixe le contrat).
3. **#201 front** — AdminGroups + AdminInscriptions (libellés, effets).
4. **#202** → **#203** → **#204** → **#206** — finitions AdminGroups (séquentiel).
5. **#205** — AutoFillModal, à tout moment (fichier disjoint).

**Parallélisme :** #166 ∥ #201-back ; #205 ∥ tout ; le reste séquentiel sur
`AdminGroups.vue`.

---
sprint: 20
nom: "Transverse : erreurs API & routing"
specs:
  - specs/technical/routing-context.md
  - specs/screens/admin-shell.md
modules:
  - specs/transverse/erreurs-api.md
  - frontend/app/src/composables/useApi.ts
  - frontend/app/src/lib/apiError.ts
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminInscriptions.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/
tickets-tag: sprint-20
branche: claude/sprint/20-transverse-erreurs-routing
branche-parent: main
log: backlog/sprints/20-transverse-erreurs-routing/log.md
---

# Sprint 20 — Transverse : erreurs API & routing

**Objectif :** Combler la dette transverse identifiée par l'audit : **écrire la
spec erreurs API** (le `[[useapi-401]]` fantôme d'admin-shell) et l'appliquer
(401 → `/login`, `extractApiError` partout, plus de messages bruts `[400] …`),
remettre le routage en cohérence (« Sélectionner » sur Tournoi), et nettoyer
les compteurs de sidebar et le code mort front.

> Origine : audit externe specs ↔ code admin (2026-07-02). La spec transverse
> « erreurs API » est annoncée par `admin-panel-map.md` depuis sa création —
> ce sprint la matérialise.

## Définition de terminé

- **Spec :** `specs/transverse/erreurs-api.md` existe, référencée dans l'INDEX ;
  `admin-shell.md` pointe vers elle (plus de lien mort `[[useapi-401]]`).
- **Golden path 401 :** session expirée → tout appel API renvoie l'utilisateur
  vers `/login` (401 JSON comme redirection HTML).
- **Golden path erreurs :** une erreur métier (ex. retrait refusé) affiche le
  **message du serveur** sur tous les écrans admin — plus jamais de
  `[400] /api/... — {json}` brut.
- « Sélectionner » (Tournoi) respecte routing-context ; compteurs sidebar sans
  « 0 » fantôme ni slots vides comptés ; plus de modales orphelines.
- Spec review `✅ Conforme` sur la nouvelle spec transverse et `admin-shell.md`.
- Aucune issue `sprint-20` ouverte (hors `en-attente`).

## Specs ciblées

- `specs/transverse/erreurs-api.md` — **à créer** (#207) : contrats `{error}`/`{fields}`, 400/401/409, conventions d'affichage
- [`specs/technical/routing-context.md`](../../../specs/technical/routing-context.md) — l'URL fait foi (#208)
- [`specs/screens/admin-shell.md`](../../../specs/screens/admin-shell.md) — compteurs (#209)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 20 — Transverse : erreurs API & routing »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#207](https://github.com/sirius911/moutilloux/issues/207) | Écrire specs/transverse/erreurs-api.md + gérer le 401 dans useApi | `specs/transverse/`, `useApi.ts` | `infra` — socle du sprint |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#17](https://github.com/sirius911/moutilloux/issues/17) | extractApiError non utilisé dans plusieurs modales/écrans | écrans + modales | Issue historique (024) ; dépend des conventions de #207 |
| [#20](https://github.com/sirius911/moutilloux/issues/20) | useApi : logs de débogage laissés en production | `useApi.ts` | Issue historique (027), `infra` — avec #207 (même fichier) |
| [#208](https://github.com/sirius911/moutilloux/issues/208) | « Sélectionner » (Tournoi) mute le store (routing-context) | `AdminTournoi.vue`, `stores/event.ts` | `infra` (store) — trancher UI vs navigation |
| [#209](https://github.com/sirius911/moutilloux/issues/209) | Compteurs sidebar : slots fixes, « 0 » avant chargement | `AdminLayout.vue` | |
| [#177](https://github.com/sirius911/moutilloux/issues/177) | GenerateMatchesModal.vue orphelin | `components/modals/` | Issue existante réutilisée |
| [#210](https://github.com/sirius911/moutilloux/issues/210) | CategoryModal / CourtModal orphelins (décisions 11-13) | `components/modals/` | Avec #177 (même geste) |

---

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/composables/useApi.ts` — #207 et #20 : **orchestrateur**,
  une seule intervention (401 + retrait des logs).
- `frontend/app/src/stores/event.ts` — #208 si la résolution touche le store.
- **Contention** : #17 touche de nombreux fichiers (petites retouches par
  écran) — à passer **après** #207 pour appliquer la convention fraîchement
  écrite, en une seule passe.

## Ordre d'exécution suggéré

1. **#207** — écrire la spec, puis implémenter 401 dans `useApi`
   (orchestrateur) ; embarquer **#20** dans la même intervention.
2. **#17** — passe d'uniformisation `extractApiError` sur tous les écrans admin
   (convention posée par #207).
3. **#208** — cohérence « Sélectionner » (décision produit à trancher dans
   l'issue avant code).
4. **#209** ∥ **#177+#210** — compteurs et suppression du code mort, en
   parallèle (fichiers disjoints).

---
sprint: 25
nom: "Arbitre : fins spéciales & résilience"
specs:
  - specs/technical/cycle-de-vie-match.md
  - specs/screens/arbitre-match.md
modules:
  - live/models.py
  - live/admin_views.py
  - live/referee_views.py
  - live/api_views.py
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/types/index.ts
tickets-tag: sprint-25
branche: claude/sprint/25-arbitre-fins-speciales
branche-parent: main
log: backlog/sprints/25-arbitre-fins-speciales/log.md
---

# Sprint 25 — Arbitre : fins spéciales & résilience

**Objectif :** Donner à l'arbitre, depuis sa tablette, tout ce qu'un jour de
tournoi exige : déclarer un **forfait** (joueur absent), un **abandon** (score
figé), une **annulation** — avec `Match.end_reason` comme support — plus le
**tiroir Corrections** (jeux±, sets±, serveur, swap d'affichage) et une saisie
qui **survit au wifi instable** (la modale Terminer ne se ferme que sur
succès).

> Origine : c'est le chantier réservé par le doc du **sprint 16** (« Hors
> périmètre (Sprint 17) : end_reason, forfait/abandon/annulation depuis la
> tablette, tiroir Corrections… ») resté non planifié — dernier trou
> fonctionnel identifié par l'audit du 2026-07-06. S'appuie sans redupliquer
> sur le sprint 16 (`start` partagé, états de l'écran, `formatLabel`, reopen
> non destructeur) et le sprint 17 (garde FINISHED ⇒ vainqueur, invariant
> mono-LIVE). Les actions back du tiroir Corrections **existent toutes**
> (`game_*_plus/minus`, `set_*`, `toggle_service`, `swap`) — #283 est du pur
> câblage. Distinct du forfait d'**entry** (sprint 12, cascade épreuve) : ici
> tout est **scopé au match**.

## Définition de terminé

- **Golden path forfait :** match PRÉVU, un joueur absent → « Déclarer
  forfait » sur la tablette → choisir le présent → match TERMINÉ libellé
  « Forfait », score de convention, **à sa place** au calendrier, classement
  recalculé, tableau/P3 synchronisés.
- **Golden path abandon :** match EN DIRECT à 3-2 → Terminer → bascule
  « Abandon adverse » + vainqueur → match TERMINÉ libellé « Abandon »,
  **score 3-2 conservé** (pas de complétion).
- **Golden path annulation :** deux absents → « Annuler le match »
  (confirmation) → CANCELED sans vainqueur, colonne « Annulés » de l'admin,
  exclu du classement.
- **Golden path corrections :** tiroir → jeux± / sets± par côté ; serveur
  refusé hors 0-0 (toast) ; jeu± refusé en tie-break (toast) ; `swap`
  n'inverse **que l'affichage** (un tap à gauche après swap crédite le bon
  joueur).
- **Golden path résilience :** couper le wifi, choisir un vainqueur → la
  modale **reste ouverte** avec l'erreur ; wifi rétabli, re-taper → succès.
  Aucune action perdue silencieusement.
- Spec review `✅ Conforme` sur `arbitre-match.md` et `cycle-de-vie-match.md`
  (dont la table « champs » : `end_reason` livré).
- Aucune issue `sprint-25` ouverte (hors `en-attente`) — #8 close.

## Specs ciblées

- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) — transitions forfait/abandon/annulation, end_reason, services partagés
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) — modes de l'écran, tiroir Corrections, modal Terminer, toasts

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 25 — Arbitre : fins spéciales & résilience »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#279](https://github.com/sirius911/moutilloux/issues/279) | Back : `Match.end_reason` + `endReason` dans `_pack_match` | `models.py`, `api_views.py`, migration | `infra` — socle |
| [#280](https://github.com/sirius911/moutilloux/issues/280) | Back : forfait & annulation scopés au match (services + actions arbitre) | `admin_views.py`, `referee_views.py` | `infra` (services) ; dépend de #279 |
| [#281](https://github.com/sirius911/moutilloux/issues/281) | Back : abandon (RETIREMENT, score figé) dans la fin manuelle | `referee_views.py`, `admin_views.py` | Dépend de #279 |
| [#282](https://github.com/sirius911/moutilloux/issues/282) | Front : actions Forfait / Annuler sur match PRÉVU | `ArbitreMatch.vue` | Dépend de #280 |
| [#285](https://github.com/sirius911/moutilloux/issues/285) | Front : modal Terminer enrichi (« Mène » + « Abandon adverse ») | `ArbitreMatch.vue` | Dépend de #281 |
| [#283](https://github.com/sirius911/moutilloux/issues/283) | Front : tiroir « Corrections » (jeux±, sets±, serveur, swap) | `ArbitreMatch.vue` | Actions back existantes — pur câblage |
| [#8](https://github.com/sirius911/moutilloux/issues/8) | Front : modale Terminer se ferme même si sendAction échoue (030) | `ArbitreMatch.vue` | Issue historique réutilisée — résilience réseau |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#284](https://github.com/sirius911/moutilloux/issues/284) | Front : libellés Forfait / Abandon en FINISHED | `ArbitreMatch.vue`, `ArbitreHome.vue` | Dépend de #279 |

---

## Périmètre backend

- **#279** — migration `end_reason` + câblage des chemins existants (fin
  auto/manuel → NORMAL, walkovers de `withdraw_entry` → WALKOVER) + packer.
- **#280** — services `forfait_match` / `cancel_match` (une seule vérité,
  consommables plus tard par l'admin) + actions `forfait`/`annuler` de
  `referee_action` avec leurs gardes.
- **#281** — paramètre `retirement` de la fin manuelle (score figé).
- Recalculs : réutiliser les chemins standings/bracket/P3/close_event
  existants — **ne rien réimplémenter**.

## Fichiers partagés (orchestrateur uniquement)

- `live/admin_views.py` — services mutualisés (#280, #281) : orchestrateur ou
  séquence stricte.
- **Contention front massive** : `ArbitreMatch.vue` est touché par #282, #283,
  #285, #8 et #284 → **strictement séquentiel** (un seul agent à la fois).
  Ordre conseillé : #8 (le socle d'erreurs sert aux suivants) → #283 → #282 →
  #285 → #284.

## Ordre d'exécution suggéré

1. **#279** — end_reason (socle, débloque tout).
2. **#280** ∥ **#281** — les transitions back (blocs distincts de
   `referee_views`/`admin_views`, séquencer si même agent).
3. **#8** — résilience des actions (modale/toasts) : à faire **avant** les
   nouveaux fronts pour qu'ils naissent avec le bon pattern d'erreur.
4. **#283** — tiroir Corrections (indépendant d'end_reason).
5. **#282** → **#285** → **#284** — les fins spéciales côté UI.

**Parallélisme :** back (#279 → #280 ∥ #281) ; front strictement séquentiel
sur `ArbitreMatch.vue`.

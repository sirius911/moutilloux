---
sprint: 44
nom: "Correctifs retours du 12 juillet"
specs:
  - specs/transverse/affichage-participant.md
  - specs/screens/tv-live.md
  - specs/screens/admin-tableau-final.md
  - specs/technical/cycle-de-vie-epreuve.md
  - specs/screens/admin-tournoi.md
  - specs/screens/admin-matchs.md
modules:
  - frontend/app/src/utils/participants.ts
  - frontend/app/src/stores/event.ts
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/tv/TvPalmares.vue
  - frontend/app/src/views/tv/TvTicker.vue
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/admin/AdminBracket.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - live/admin_views.py
  - live/bracket.py
tickets-tag: sprint-44
branche: claude/sprint/44-retours-12-juillet
branche-parent: main
log: backlog/sprints/44-retours-12-juillet/log.md
---

# Sprint 44 — Correctifs retours du 12 juillet

**Objectif :** résorber les 5 retours produit du 2026-07-12 — le vainqueur TV
affiché dès la finale terminée, la petite finale remise à sa place (sous la
finale, jamais de colonne fantôme, bascule tardive effective), le crash
d'AdminBracket au changement d'épreuve (qui masque le tableau du Double), la
règle transverse `displayName` (fin des « TBD vs TBD » pour les doubles), et
la pastille d'épreuve compacte au planning.

> Origine : retours produit du 2026-07-12, analyse + 4 arbitrages rendus le
> jour même. Specs mises à jour en séance (commit `5b53f3a`) :
> [[affichage-participant]] créée, §« Slides — Tableau » et §« État PALMARÈS »
> de [[tv-live]], §« Le bracket » d'[[admin-tableau-final]] (P3 sous la
> finale, étapes absentes sans colonne), §« Petite finale » de
> [[cycle-de-vie-epreuve]] (bascule tardive), ligne « Petite finale » de la
> modale Épreuve d'[[admin-tournoi]], pastille compacte + noms `displayName`
> d'[[admin-matchs]]. S'appuie sur le sprint 43 (palmarès #374, garde
> d'identité du store live #370) sans le redupliquer.

## Définition de terminé

- **Vainqueur TV** : finale terminée → la slide Tableau du carousel affiche le
  nom du vainqueur sous le trophée (accent) ; finale non jouée → « À DÉSIGNER ».
- **Forme du tableau (TV + admin)** : épreuve sans petite finale → aucune
  mention « 3e place » nulle part ; tableau qui démarre en demies → pas de
  colonne Quarts ; épreuve avec P3 → le match s'affiche sous la finale, dans
  la même colonne (admin et TV).
- **Changement d'épreuve** : sélecteur Simple Principal → Double sur la page
  Tableau final → aucune erreur console, l'écran affiche le tableau du Double
  (demies + finale) sans rechargement.
- **Bascule tardive** : demies terminées → activer la petite finale dans la
  modale Épreuve → le match P3 apparaît (admin + TV) avec les deux perdants ;
  P3 lancé → la désactivation renvoie 400 et le message s'affiche dans la
  modale.
- **Doubles** : le planning affiche les noms d'équipes (« X / Y vs … ») pour
  tous les matchs du Double ; plus aucun « TBD » ni `player?.fullName` de
  participant dans les 10 fichiers du sweep.
- **Pastille** : planning multi-épreuves → pastille d'épreuve compacte, noms
  et boutons alignés ; mono-épreuve inchangé.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur les 6 specs ciblées.
- Aucune issue `sprint-44` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/transverse/affichage-participant.md`](../../../specs/transverse/affichage-participant.md) —
  la règle `displayName` → étiquette de provenance → « À désigner », le helper
  unique, le périmètre du sweep et ses exceptions.
- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) —
  §« Slides — Tableau » (colonne VAINQUEUR, 3e place sous la finale, jamais de
  bloc fantôme), §« État PALMARÈS » (même disposition).
- [`specs/screens/admin-tableau-final.md`](../../../specs/screens/admin-tableau-final.md) —
  §« Le bracket » : étapes hors forme du tableau sans colonne, petite finale
  sous la finale, nommage des places.
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) —
  §« Petite finale » : bascule tardive (effet immédiat rétroactif).
- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md) —
  ligne « Petite finale » de la modale Épreuve (comportement après Débuter).
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) —
  pastille d'épreuve compacte, noms de ligne selon [[affichage-participant]].

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 44 — Correctifs retours du
> 12 juillet »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#383](https://github.com/sirius911/moutilloux/issues/383) | Front : TvIdle — colonne VAINQUEUR : nom du vainqueur dès la finale terminée | `TvIdle.vue` | après #388 (helper) ; même fichier que #384 |
| [#384](https://github.com/sirius911/moutilloux/issues/384) | Front : TV — mini-bracket conforme à la forme du tableau (3e place sous la finale, plus de colonne fantôme) | `TvIdle.vue`, `TvPalmares.vue` | même fichier que #383 : même agent |
| [#385](https://github.com/sirius911/moutilloux/issues/385) | Front : AdminBracket — crash au rendu d'un slot sans match (écran figé sur l'ancienne épreuve) | `AdminBracket.vue` | avec #386 et #389 : même agent |
| [#386](https://github.com/sirius911/moutilloux/issues/386) | Front : AdminBracket — étapes hors forme du tableau : pas de colonne | `AdminBracket.vue` | avec #385 |
| [#387](https://github.com/sirius911/moutilloux/issues/387) | Back : petite finale — bascule tardive effective (création/suppression du P3) | `live/admin_views.py`, `live/bracket.py` | `infra` — services mutualisés, indépendant du front |
| [#388](https://github.com/sirius911/moutilloux/issues/388) | Front : règle affichage-participant — helper sideName() + sweep displayName | `utils/participants.ts` (à créer) + 10 fichiers | `infra` — helper par l'orchestrateur, en premier |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#389](https://github.com/sirius911/moutilloux/issues/389) | Front : AdminBracket — petite finale sous la finale (plus de colonne dédiée) | `AdminBracket.vue` | avec #385/#386 : même passe |
| [#390](https://github.com/sirius911/moutilloux/issues/390) | Front : AdminMatches — pastille d'épreuve compacte | `AdminMatches.vue` | indépendant |
| [#391](https://github.com/sirius911/moutilloux/issues/391) | Front : store event — ignorer les réponses périmées au changement d'épreuve | `stores/event.ts` | `infra` — orchestrateur, patron du #370 |

---

## Périmètre backend

- `live/admin_views.py` (#387) : dans `update_event`, réagir au changement de
  `has_third_place` — création du P3 + `sync_p3_losers_for_event` à
  l'activation, suppression si `SCHEDULED` / `ValueError` sinon à la
  désactivation.
- `live/bracket.py` (#387) : extraire la création du slot P3
  (`bracket.py:198-209`) en fonction réutilisable — pas de duplication.
- Aucune route nouvelle : `api_event_edit` existe déjà, pas de câblage
  `live/urls.py`. Aucun changement front (la modale Épreuve affiche déjà les
  erreurs serveur).

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/utils/participants.ts` (#388, à créer) — helper consommé
  par tous les écrans : l'orchestrateur le crée **en premier**, les agents
  d'écran l'utilisent ensuite.
- `frontend/app/src/stores/event.ts` (#391) — store Pinia partagé :
  orchestrateur.
- `live/admin_views.py` / `live/bracket.py` (#387) — services mutualisés : un
  seul agent back dessus à la fois.

## Ordre d'exécution suggéré

1. **Socle (orchestrateur)** : #388-helper (création de `sideName()`, sans le
   sweep) puis #391 (petit, même zone de fiabilité) ∥ **#387** (back,
   fichiers disjoints).
2. **Écrans en parallèle** (fichiers disjoints entre agents) :
   - agent A : #385 + #386 + #389 (AdminBracket, même fichier, une passe) —
     adopter `sideName()` au passage ;
   - agent B : #383 + #384 (TvIdle + TvPalmares, même zone mini-bracket) —
     adopter `sideName()` au passage ;
   - agent C : #390 (AdminMatches, pastille) — adopter `sideName()` au
     passage (c'est le fix du « TBD vs TBD »).
3. **Reste du sweep #388** : fichiers non couverts par les agents d'écran
   (TvTicker, TvScoreboard, AdminRegie, ArbitreHome, ArbitreMatch,
   EditMatchPanel) — parallélisable une fois le helper posé ; clore #388
   quand plus aucune occurrence ne subsiste.
4. **Vérification** : golden paths de la Définition de terminé sur les 3
   cibles d'écran (desktop admin, TV 1080p ; l'arbitre n'est touché que par
   le sweep), `vue-tsc`, spec review des 6 specs.

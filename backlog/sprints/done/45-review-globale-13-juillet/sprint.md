---
sprint: 45
nom: "Correctifs review globale du 13 juillet"
specs:
  - specs/screens/admin-shell.md
  - specs/screens/admin-tournoi.md
  - specs/screens/admin-regie-mobile.md
  - specs/transverse/erreurs-api.md
  - specs/technical/planning.md
  - specs/technical/cycle-de-vie-match.md
  - specs/technical/cycle-de-vie-epreuve.md
modules:
  - frontend/app/src/views/admin/AdminLayout.vue
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/views/admin/AdminRegie.vue
  - frontend/app/src/views/arbitre/ArbitreHome.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/views/admin/AdminBracket.vue
  - frontend/app/src/views/tv/TvTicker.vue
  - frontend/app/src/components/modals/PlayDayModal.vue
  - frontend/app/src/components/modals/EditMatchPanel.vue
  - frontend/app/src/stores/event.ts
  - live/models.py
  - live/api_views.py
  - live/admin_views.py
tickets-tag: sprint-45
branche: claude/sprint/45-review-globale-13-juillet
branche-parent: main
log: backlog/sprints/45-review-globale-13-juillet/log.md
---

# Sprint 45 — Correctifs review globale du 13 juillet

**Objectif :** résorber les 10 anomalies relevées par la review globale
exploratoire du 2026-07-13 (test manuel de bout en bout des 12 écrans,
admin + arbitre + TV) : compteurs de sidebar faux ou morts, heures estimées
au-delà de minuit non normalisées (jusque sur la TV publique), erreurs API
affichées brutes, annonces et teinte de ponctualité inertes en régie mobile,
état hybride « Prévu avec vainqueur » non gardé — plus quatre correctifs
cosmétiques (ordre des annonces, dates ISO, double tilde, petite finale
sans demies).

> Origine : review globale du 2026-07-13 (session interactive « utilisateur
> testeur »). Le détail des constats, causes et lignes est dans chaque issue.
> Résidus de tickets clos assumés : #397 prolonge #375/#380 (ETA à la lecture),
> #403 prolonge #368 (reopen remet finished_at à NULL) — issues neuves ciblées,
> pas de réouverture.

## Définition de terminé

- **Sidebar** : arriver sur `/admin/tournoi` après connexion → les compteurs
  Inscriptions/Poules/Planning/Tableau final affichent les comptes réels de
  l'épreuve active (jamais « 0 » par défaut, jamais de badge éternellement
  vide).
- **Heures** : aucune surface (calendrier admin, panneau, régie, arbitre, TV)
  n'affiche d'heure ≥ 24:00 ni de « ~~ » double tilde ; l'en-tête de journée
  et la pastille de capacité restent plausibles avec un match fini après
  minuit ou re-planifié un autre jour.
- **Erreurs** : suppression d'une journée portant une pause → seul le message
  serveur s'affiche (pas d'enveloppe `[409] /api/... — {json}`) ; plus aucune
  copie locale d'`extractError` (import `lib/apiError.ts` partout).
- **Régie mobile** : rechargement direct de `/admin/regie` → les annonces de
  l'édition s'affichent ; un match planifié en retard porte sa teinte de
  ponctualité.
- **Statut** : passer un match Terminé → Prévu ne laisse plus de vainqueur ni
  d'horodatage de fin (ou est refusé, selon l'arbitrage de #403) ; le match 51
  est corrigé en base ; bracket, calendrier et TV racontent la même histoire.
- **Cosmétique** : nouvelle annonce en tête de liste ; dates d'édition en
  français ; petite finale refusée avec message sur un tableau sans demies.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur les specs ciblées (compléter planning.md
  — heures > minuit — et cycle-de-vie-match.md — Terminé → Prévu — au passage).
- Aucune issue `sprint-45` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-shell.md`](../../../specs/screens/admin-shell.md) —
  compteurs de navigation (comptes réels, état neutre, jamais « 0 »).
- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md) —
  annonces en tête de liste, format des dates, ligne « Petite finale ».
- [`specs/screens/admin-regie-mobile.md`](../../../specs/screens/admin-regie-mobile.md) —
  section Annonces, teinte de ponctualité.
- [`specs/transverse/erreurs-api.md`](../../../specs/transverse/erreurs-api.md) —
  `extractApiError` fonction unique d'affichage.
- [`specs/technical/planning.md`](../../../specs/technical/planning.md) —
  ETA serveur à la lecture, format des heures publiques (à compléter :
  représentation au-delà de minuit, préfixe « ~ » canonique).
- [`specs/technical/cycle-de-vie-match.md`](../../../specs/technical/cycle-de-vie-match.md) —
  transitions de statut (à compléter : Terminé → Prévu).
- [`specs/technical/cycle-de-vie-epreuve.md`](../../../specs/technical/cycle-de-vie-epreuve.md) —
  petite finale (cas tableau sans demies, à compléter).

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 45 — Correctifs review globale
> du 13 juillet »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#394](https://github.com/sirius911/moutilloux/issues/394) | Front : AdminLayout — compteurs sidebar : état neutre, comptes réels, badge Planning mort | `AdminLayout.vue`, `stores/event.ts` | `infra` — store partagé : orchestrateur |
| [#397](https://github.com/sirius911/moutilloux/issues/397) | Back+Front : ETA — normaliser les heures au-delà de minuit | `live/admin_views.py` (service ETA), `AdminMatches.vue` | `infra` — service mutualisé ; arbitrage sur la représentation |
| [#399](https://github.com/sirius911/moutilloux/issues/399) | Front : erreurs API brutes — généraliser extractApiError + résorber les copies locales | `PlayDayModal.vue`, `AdminMatches.vue`, `ArbitreMatch.vue`, `AdminRegie.vue`, `AdminBracket.vue` | mécanique, parallélisable par fichier |
| [#401](https://github.com/sirius911/moutilloux/issues/401) | Front : AdminRegie — annonces jamais chargées en accès direct | `AdminRegie.vue` | pattern AdminTournoi (watch) ; même fichier que #402 |
| [#403](https://github.com/sirius911/moutilloux/issues/403) | Back : statut Terminé → Prévu — purger vainqueur/horodatages | `live/admin_views.py` | `infra` — service mutualisé ; arbitrage A/B + correction du match 51 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#395](https://github.com/sirius911/moutilloux/issues/395) | Back : Announcement — nouvelle annonce en tête de liste | `live/models.py` | une ligne + migration |
| [#396](https://github.com/sirius911/moutilloux/issues/396) | Front : AdminTournoi — dates d'édition au format français | `AdminTournoi.vue` | indépendant |
| [#398](https://github.com/sirius911/moutilloux/issues/398) | Front/Back : double tilde « ~~HH » — format canonique du préfixe ~ | `EditMatchPanel.vue`, `AdminRegie.vue`, `ArbitreHome.vue`, `TvTicker.vue`, packers | `infra` si option serveur ; **avant** #402 |
| [#400](https://github.com/sirius911/moutilloux/issues/400) | Back : petite finale sans demi-finales — refus explicite | `live/admin_views.py` | s'appuie sur #387 (sprint 44) |
| [#402](https://github.com/sirius911/moutilloux/issues/402) | Front : AdminRegie — teinte de ponctualité morte (parsing) | `AdminRegie.vue` | **après** #398 (format canonique) ; même fichier que #401 |

---

## Périmètre backend

- `live/models.py` (#395) : `Announcement.Meta.ordering = ["-created_at"]`
  + migration.
- `live/admin_views.py` :
  - #397 — normalisation des heures dans le service ETA (`compute_day_eta_map`),
    ancrage du curseur sur la date de la journée, exposer la fin de journée
    estimée dans le payload calendar ;
  - #400 — refus `ValueError` → 400 de la petite finale sans demies (réutilise
    le service du #387) ;
  - #403 — purge `winner_side`/`finished_at`/`end_reason` au retour Prévu
    (ou interdiction, selon arbitrage) + correction de la donnée du match 51.
- `live/api_views.py` (#398, si option serveur retenue) : retirer le « ~ » des
  packers, les clients préfixent à l'affichage.
- Aucune route nouvelle : pas de câblage `live/urls.py`.

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/stores/event.ts` (#394) — chargement des comptes +
  purge kanban/fetchMatches : orchestrateur.
- `live/admin_views.py` (#397, #400, #403) — services mutualisés : un seul
  agent back à la fois (trois tickets, une même passe back recommandée).
- Packers `live/api_views.py` (#398) — décision de format prise par
  l'orchestrateur avant les correctifs d'écrans (#398 clients, #402).

## Ordre d'exécution suggéré

1. **Arbitrages (orchestrateur, avant tout code)** : représentation des heures
   > minuit (#397), format canonique du « ~ » (#398), option A/B du statut
   (#403) — trois décisions qui conditionnent le reste ; compléter les specs.
2. **Passe back unique** : #395 (une ligne) + #397 + #400 + #403
   (`live/…` — fichiers partagés, séquentiel).
3. **Écrans en parallèle** (fichiers disjoints) :
   - agent A : #394 (AdminLayout + store — orchestrateur pour la partie store) ;
   - agent B : #401 + #402 (AdminRegie, même fichier, une passe — #402 après
     la décision #398) ;
   - agent C : #399 (sweep extractApiError sur 5 fichiers) + #398 côté clients
     (4 fichiers, recoupe ArbitreMatch/AdminRegie : coordonner avec B) ;
   - agent D : #396 (AdminTournoi, trivial).
4. **Vérification** : golden paths de la Définition de terminé (desktop admin,
   mobile régie, TV 1080p), `vue-tsc`, spec review des specs ciblées.

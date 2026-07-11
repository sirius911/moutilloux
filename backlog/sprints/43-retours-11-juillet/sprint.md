---
sprint: 43
nom: "Correctifs retours du 11 juillet"
specs:
  - specs/screens/tv-live.md
  - specs/technical/tv-state.md
  - specs/screens/arbitre-match.md
  - specs/screens/admin-inscriptions.md
  - specs/technical/planning.md
modules:
  - frontend/app/src/composables/usePolling.ts
  - frontend/app/src/stores/live.ts
  - frontend/app/src/views/tv/TvScoreboard.vue
  - frontend/app/src/views/tv/TvIdle.vue
  - frontend/app/src/views/tv/TvTicker.vue
  - frontend/app/src/views/tv/TvPalmares.vue
  - frontend/app/src/views/arbitre/ArbitreMatch.vue
  - frontend/app/src/components/modals/CreateTeamModal.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - live/referee_views.py
  - live/admin_views.py
  - live/api_views.py
  - live/models.py
tickets-tag: sprint-43
branche: claude/sprint/43-retours-11-juillet
branche-parent: main
log: backlog/sprints/43-retours-11-juillet/log.md
---

# Sprint 43 — Correctifs retours du 11 juillet

**Objectif :** résorber les 8 retours produit du 2026-07-11 — deux bugs de
fond (le `finished_at` jamais persisté qui casse « Derniers résultats », les
timers de polling qui s'empilent et fuient : carrousel accéléré + blink
arbitre), deux features TV arbitrées (banderole d'information pendant le
match, écran PALMARÈS de fin d'édition), l'indicateur de service arbitre,
la garde équipe Double, et le passage des ETA au **calcul serveur à la
lecture** (l'heure courante recale enfin les horaires publics).

> Origine : retours produit du 2026-07-11, analyse + 4 arbitrages rendus le
> jour même. Specs mises à jour en séance : §« Banderole d'information » et
> §« État PALMARÈS » de [[tv-live]], `events[].status` + poll continu dans
> [[tv-state]], indicateur de service imposant + étanchéité du polling dans
> [[arbitre-match]], règle « un joueur, une équipe par épreuve » dans
> [[admin-inscriptions]], §« Où vit le calcul » (ETA à la lecture) dans
> [[planning]]. S'appuie sur les sprints 22 (annonces), 30 (moteur ETA front),
> 35/39/42 (scènes TV) sans les redupliquer.

## Définition de terminé

- **Derniers résultats** : terminer un match sur balle de match → il apparaît
  en tête de la slide « Derniers résultats » ; plus aucun match `FINISHED`
  avec `finished_at NULL` en base (backfill passé).
- **Stabilité polling** : après un match et plusieurs cycles onglet
  caché/visible, chaque slide du carrousel tient ses ~8 s pleines ; naviguer
  match A → accueil → match B ne montre plus jamais une donnée du match A ni
  de requêtes réseau vers A.
- **Banderole** : match LIVE avec ≥1 annonce active → la banderole défile
  sous la bande de score (annonces · résultats · programme) sans recouvrir
  les lignes joueurs ; sans contenu, pied discret inchangé.
- **Palmarès** : finale de la dernière épreuve jouée → après la fenêtre fin
  de match, l'écran palmarès s'installe (poules à gauche, tableau et
  vainqueur en avant à droite) et ne cède plus au carrousel ; une réouverture
  de match reprend l'antenne.
- **ETA** : un match qui déborde → au poll suivant, les ~heures de l'aval
  reculent sur la TV (programme + « À préparer ») sans action admin.
- **Double** : créer A/B puis tenter A/C sur la même épreuve → 400 + message ;
  A et B absents des sélecteurs de la modale.
- **Arbitre** : la balle de service grand format + nom du serveur en accent,
  scènes iPad et mobile, cohérents avec `toggle_service` et `swap`.
- `npx vue-tsc --noEmit` passe.
- Spec review `✅ Conforme` sur les 5 specs ciblées.
- Aucune issue `sprint-43` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/tv-live.md`](../../../specs/screens/tv-live.md) —
  §« Banderole d'information (ticker) », §« État PALMARÈS », bascule d'état,
  états limites ; §« Bascule d'état » (reprise de rotation, déjà spécifiée).
- [`specs/technical/tv-state.md`](../../../specs/technical/tv-state.md) —
  `events[].status`, poll `tv/idle` continu porté par l'écran, `scheduledTime`
  = ETA à la lecture.
- [`specs/screens/arbitre-match.md`](../../../specs/screens/arbitre-match.md) —
  indicateur de service imposant, étanchéité du polling.
- [`specs/screens/admin-inscriptions.md`](../../../specs/screens/admin-inscriptions.md) —
  règle « un joueur, une équipe par épreuve ».
- [`specs/technical/planning.md`](../../../specs/technical/planning.md) —
  §« Où vit le calcul » (ETA serveur à la lecture).

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 43 — Correctifs retours du
> 11 juillet »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#367](https://github.com/sirius911/moutilloux/issues/367) | Back : fin automatique de match — finished_at jamais persisté (+ backfill) | `live/referee_views.py`, `live/models.py` | indépendant |
| [#369](https://github.com/sirius911/moutilloux/issues/369) | Front : usePolling — démarrage gardé, arrêt total, pas de chevauchement ni de fuite | `composables/usePolling.ts` | `infra` — orchestrateur |
| [#370](https://github.com/sirius911/moutilloux/issues/370) | Front : store live — fetchMatch ignore les réponses périmées | `stores/live.ts` | `infra` — orchestrateur, avec #369 |
| [#371](https://github.com/sirius911/moutilloux/issues/371) | Front : TV — polling tv/idle porté par l'écran | `TvScoreboard.vue`, `TvIdle.vue` | `infra` — prérequis de #372 et #374 |
| [#372](https://github.com/sirius911/moutilloux/issues/372) | Front : TV — banderole d'information pendant le match | `TvTicker.vue` (à créer), `TvScoreboard.vue` | après #371 |
| [#373](https://github.com/sirius911/moutilloux/issues/373) | Back : tv/idle — exposer events[].status | `live/api_views.py` | prérequis de #374 |
| [#374](https://github.com/sirius911/moutilloux/issues/374) | Front : TV — état PALMARÈS (édition terminée) | `TvPalmares.vue` (à créer), `TvScoreboard.vue` | après #371 et #373 |
| [#375](https://github.com/sirius911/moutilloux/issues/375) | Back : ETA à la lecture — service commun + scheduledTime recalé | `live/admin_views.py`, `live/api_views.py` | `infra` — corrige la TV sans changement front |
| [#376](https://github.com/sirius911/moutilloux/issues/376) | Front : ArbitreMatch — balle de service imposante + nom du serveur en avant | `ArbitreMatch.vue` | indépendant |
| [#377](https://github.com/sirius911/moutilloux/issues/377) | Back : Double — refuser un joueur déjà engagé dans une équipe de l'épreuve | `live/admin_views.py` | indépendant |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#368](https://github.com/sirius911/moutilloux/issues/368) | Back : reopen_match — remettre finished_at à NULL | `live/admin_views.py` | même cause racine que #367 : se closent ensemble |
| [#378](https://github.com/sirius911/moutilloux/issues/378) | Front : CreateTeamModal — exclure les joueurs déjà en équipe | `CreateTeamModal.vue`, `AdminInscriptions.vue` | après #377 (contrat d'erreur) |
| [#379](https://github.com/sirius911/moutilloux/issues/379) | Front : TvIdle — reprendre la rotation là où elle s'était arrêtée | `TvIdle.vue` | même zone que #371 : à traiter ensemble |
| [#380](https://github.com/sirius911/moutilloux/issues/380) | Front : AdminMatches — afficher les ETA serveur | `AdminMatches.vue` | après #375 |

---

## Périmètre backend

- `live/referee_views.py` + `live/models.py` (#367) : persistance de
  `finished_at` sur la fin automatique + migration de backfill
  (`finished_at := updated_at` pour les FINISHED à NULL).
- `live/admin_views.py` : clear de `finished_at` dans `reopen_match` (#368),
  garde équipe Double dans `create_team_with_entry` / `replace_entry_player`
  / `add_late_entry` (#377), **fonction de service ETA** (#375).
- `live/api_views.py` : `events[].status` dans `_pack_tv_events` (#373),
  application de l'ETA à la lecture dans les packers calendrier / tv/state /
  tv/idle / arbitre (#375).
- Aucune route nouvelle : pas de câblage `live/urls.py`.

## Fichiers partagés (orchestrateur uniquement)

- `frontend/app/src/composables/usePolling.ts` (#369) — consommé par tous les
  écrans : à traiter par l'orchestrateur, en premier.
- `frontend/app/src/stores/live.ts` (#370, et hissage éventuel de l'état de
  rotation pour #379) — orchestrateur.
- `frontend/app/src/types/index.ts` — ajout de `status` au type `TvEvent`
  (dans le périmètre de #373/#374) — orchestrateur.
- Le service ETA (#375) touche `admin_views.py`/`api_views.py` mutualisés —
  un seul agent back dessus à la fois.

## Ordre d'exécution suggéré

1. **Socle fiabilité (orchestrateur)** : #369 puis #370 (petits, débloquent la
   vérification de tout le reste) ∥ **#367** (back, fichiers disjoints).
2. **#371 (+ #379, même zone)** — hissage du polling et de la rotation ;
   ∥ **#373** et **#377** (back, indépendants).
3. **#372** (banderole) et **#374** (palmarès) — après #371/#373 ; deux SFC
   nouvelles, parallélisables entre elles (fichiers disjoints, câblage
   TvScoreboard par l'orchestrateur) ; ∥ **#376** (arbitre) ∥ **#375** (back
   ETA, gros morceau isolé).
4. **Finitions** : #368 (avec #367 si pas déjà fait), #378 (après #377),
   #380 (après #375).

---
sprint: 14
nom: Correctifs : navigation, registre, poules & journées
specs:
  - specs/screens/admin-tournoi.md
  - specs/screens/admin-joueurs.md
  - specs/screens/admin-poules.md
  - specs/screens/admin-matchs.md
  - specs/technical/planning.md
modules:
  - frontend/app/src/views/admin/AdminTournoi.vue
  - frontend/app/src/views/admin/AdminGroups.vue
  - frontend/app/src/views/admin/AdminPlayers.vue
  - frontend/app/src/views/admin/AdminMatches.vue
  - frontend/app/src/components/modals/PlayDayModal.vue
  - frontend/app/src/stores/event.ts
  - live/admin_views.py
  - live/api_views.py
  - live/urls.py
tickets-tag: sprint-14
branche: claude/sprint/14-correctifs
branche-parent: main
log: backlog/sprints/14-correctifs/log.md
---

# Sprint 14 — Correctifs : navigation, registre, poules & journées

**Objectif :** Résoudre 6 problèmes remontés en usage réel — routes de navigation
mortes (Tournoi, Poules), registre joueurs (colonnes contact + âge + bug
`birth_year`), composition manuelle des poules, et la vraie UI de gestion des
journées de jeu (fin du renvoi vers l'admin Django).

## Définition de terminé

- **Golden path navigation :** depuis Tournoi, les raccourcis Inscriptions / Poules
  / Matchs ouvrent le bon écran de l'épreuve (`/admin/events/:eventId/…`), plus
  jamais le scoreboard TV ; idem pour « Voir le Calendrier » du bandeau Poules.
- **Golden path joueurs :** créer un joueur avec une année de naissance → la colonne
  « Âge » l'affiche immédiatement (sans ré-édition) ; colonnes Téléphone et Email
  visibles.
- **Golden path poules :** « + Nouvelle poule » crée une poule vide ; on dispatche
  les inscrits à la main avant de débuter, sans passer par le remplissage auto.
- **Golden path journées :** « Gérer les journées » crée / édite / supprime une
  journée depuis l'app ; suppression refusée si la journée porte des matchs/pauses ;
  l'état vide du Calendrier ne renvoie plus vers Django.
- Spec review `✅ Conforme` sur les 5 specs ciblées.
- Aucune issue `sprint-14` ouverte (hors `en-attente`).

## Specs ciblées

- [`specs/screens/admin-tournoi.md`](../../../specs/screens/admin-tournoi.md) — raccourcis d'épreuve (routing)
- [`specs/screens/admin-joueurs.md`](../../../specs/screens/admin-joueurs.md) — colonnes contact + Âge, contrat `birth_year`
- [`specs/screens/admin-poules.md`](../../../specs/screens/admin-poules.md) — « + Nouvelle poule », lien Calendrier
- [`specs/screens/admin-matchs.md`](../../../specs/screens/admin-matchs.md) — modale « Gérer les journées »
- [`specs/technical/planning.md`](../../../specs/technical/planning.md) — `CRUD PlayDay`
- Voir aussi : [[routing-context]] (URL = source de vérité), [[admin-panel-map]] (décisions 23-24)

---

## Tickets du sprint

> Tous dans GitHub Issues (milestone « Sprint 14 — Correctifs : navigation, registre, poules & journées »).

### 🟠 Majeures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#150](https://github.com/sirius911/moutilloux/issues/150) | AdminTournoi : raccourcis Inscriptions/Poules/Matchs vers routes mortes | `AdminTournoi.vue` | Routes plates obsolètes → catch-all `/tv/live` |
| [#151](https://github.com/sirius911/moutilloux/issues/151) | AdminGroups : lien « Voir le Calendrier » vers route morte | `AdminGroups.vue` | Même cause que #150 |
| [#154](https://github.com/sirius911/moutilloux/issues/154) | api_player_create : année de naissance perdue (`birth_date` vs `birth_year`) | `live/api_views.py` | Back ; perte de donnée à la création |
| [#155](https://github.com/sirius911/moutilloux/issues/155) | AdminGroups : bouton « + Nouvelle poule » (composition manuelle) | `AdminGroups.vue` | Endpoint + `store.createGroup` déjà existants |
| [#156](https://github.com/sirius911/moutilloux/issues/156) | Back : endpoints CRUD PlayDay (gestion des journées) | `admin_views.py`, `api_views.py`, `urls.py` | ⚠️ `urls.py` câblé par l'orchestrateur. Pas de migration |
| [#157](https://github.com/sirius911/moutilloux/issues/157) | AdminMatches : modale « Gérer les journées » | `AdminMatches.vue`, `PlayDayModal.vue` (nouveau), `event.ts` | ⚠️ `event.ts` infra partagée. Dépend de #156 |

### 🟡 Mineures

| # | Titre | Fichier(s) | Note |
|---|-------|-----------|------|
| [#152](https://github.com/sirius911/moutilloux/issues/152) | AdminPlayers : colonnes Téléphone & Email manquantes | `AdminPlayers.vue` | Donnée déjà servie par `_pack_player` |
| [#153](https://github.com/sirius911/moutilloux/issues/153) | AdminPlayers : colonne « Âge » calculée (remplace « Né(e) en ») | `AdminPlayers.vue` | Dépend de #154 pour les joueurs créés |

---

## Périmètre backend

- **#154** — corriger le champ lu par `api_player_create` (`birth_year`).
- **#156** — fonctions de service `create/update/delete_play_day` dans
  `admin_views.py` + endpoints `/api/` fins ; suppression refusée si la journée
  porte des matchs ou des pauses. **Aucune migration** (modèle `PlayDay` déjà en
  base). `live/urls.py` câblé par l'orchestrateur.

## Fichiers partagés (orchestrateur uniquement)

- `live/urls.py` — routes des endpoints `PlayDay` (#156).
- `frontend/app/src/stores/event.ts` — actions `createPlayDay` / `editPlayDay` /
  `deletePlayDay` (#157).

## Ordre d'exécution suggéré

1. **#150 / #151** — corrections de routes (indépendantes, rapides, fichiers disjoints).
2. **#154** — fix back `birth_year` (indépendant). Précède #153 pour un golden path propre.
3. **#152 / #153** — colonnes registre joueurs (même fichier `AdminPlayers.vue` → séquentiel entre eux).
4. **#155** — bouton « + Nouvelle poule » (indépendant).
5. **#156 [back]** — endpoints CRUD PlayDay + câblage `urls.py`.
6. **#157 [front]** — modale « Gérer les journées ». **Dépend de #156** + actions store (infra partagée).

**Parallélisme :** #150, #151, #154, #155 touchent des fichiers disjoints →
parallélisables. #156 → #157 est la seule chaîne de dépendance stricte.

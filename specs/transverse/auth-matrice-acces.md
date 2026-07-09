---
type: transverse
module: auth-matrice-acces
fichiers:
  - live/api_views.py
  - live/admin_views.py
  - live/referee_views.py
---

# Spec transverse — Matrice d'accès des endpoints `/api/`

> Recense le niveau d'accès de chaque endpoint `/api/...` exposé par
> `live/api_views.py`, pour éviter les dérives (endpoint mutant exposé avec un
> décorateur trop permissif). Source de vérité : le décorateur réellement posé
> sur la vue, pas une intention. Référencée par [[erreurs-api]] (contrats
> d'erreur 401/403) et à consulter avant d'ajouter un nouvel endpoint `/api/`.

## Niveaux d'accès

| Niveau | Décorateur | Qui peut appeler |
|---|---|---|
| **Public** | aucun décorateur d'auth | N'importe qui, y compris non connecté (nécessaire pour la TV/spectateur) |
| **Connecté** | `@login_required` | Tout utilisateur authentifié (Arbitre ou Admin) — à réserver aux endpoints réellement partagés entre les deux rôles |
| **Arbitre** | `@referee_required` (`live/referee_views.py:20`, `user_passes_test(is_referee)`) | Membre du groupe `Arbitre` OU superuser |
| **Superuser (admin)** | `@superuser_required` (`live/admin_views.py:31`, `user_passes_test(lambda u: u.is_authenticated and u.is_superuser)`) | Superuser uniquement |

## Matrice complète (`live/api_views.py`)

| Endpoint (route) | Vue | Niveau | Remarque |
|---|---|---|---|
| `GET /api/csrf/` | `api_csrf` | Public | Pose le cookie CSRF, doit rester accessible sans session |
| `POST /api/auth/logout/` | `api_logout` | Public* | *Pas de garde explicite ; no-op si déjà anonyme |
| `POST /api/auth/login/` | `api_login` | Public | Endpoint d'authentification lui-même |
| `GET /api/editions/` | `api_editions` | Public | Lecture nécessaire pour la TV |
| `GET /api/events/<id>/players/` | `api_event_players` | Public | Lecture TV/spectateur |
| `GET /api/events/<id>/groups/` | `api_event_groups` | Public | Lecture TV (poules) |
| `GET /api/events/<id>/matches/` | `api_event_matches` | Public | Lecture TV (calendrier) |
| `GET /api/matches/<id>/` | `api_match_detail` | Public | Lecture TV (scoreboard) |
| `GET /api/events/<id>/bracket/` | `api_event_bracket` | Public | Lecture TV (tableau final) |
| `GET /api/arbitre/matches/` | `api_arbitre_matches` | Arbitre | `@referee_required` |
| `POST /api/matches/<id>/action/` | `api_match_action` | Arbitre | Moteur de score (points, corrections, transitions) — remplace `POST /arbitre/match/<id>/action/` après suppression des vues template arbitre (retours 2026-07-09). Consommé par la SPA arbitre **et** la régie mobile admin (le niveau Arbitre inclut le superuser). |
| `GET /api/players/` | `api_players` | **Superuser** (après fix) | Était `@login_required` — corrigé par ce ticket |
| `POST /api/players/create/` | `api_player_create` | **Superuser** (après fix) | Était `@login_required` — corrigé par ce ticket |
| `GET /api/me/` | `api_me` | Public | Doit rester accessible non connecté (retourne 401 JSON attendu, géré par le front) |
| `POST /api/players/<id>/edit/` | `api_player_edit` | Superuser | Référence de cohérence pour le fix ci-dessus |
| `POST /api/events/<id>/teams/create/` | `api_team_create` | Superuser | |
| `POST /api/events/<id>/registrations/add/` | `api_registration_add` | Superuser | |
| `POST /api/events/<id>/registrations/add-bulk/` | `api_registration_add_bulk` | Superuser | |
| `POST /api/events/<id>/registrations/<entry_id>/remove/` | `api_registration_remove` | Superuser | |
| `POST /api/events/<id>/groups/create/` | `api_group_create` | Superuser | |
| `POST /api/events/<id>/groups/autofill/` | `api_groups_autofill` | Superuser | |
| `POST /api/events/<id>/matches/generate/` | `api_matches_generate` | Superuser | |
| `POST /api/events/<id>/groups/assign/` | `api_group_assign` | Superuser | |
| `POST /api/events/<id>/groups/unassign/` | `api_group_unassign` | Superuser | |
| `POST /api/matches/<id>/edit/` | `api_match_edit` | Superuser | |
| `POST /api/matches/<id>/feature/` | `api_match_feature` | Superuser | |
| `POST /api/matches/<id>/start/` | `api_match_start` | Superuser | |
| `POST /api/events/<id>/bracket/create/` | `api_bracket_create` | Superuser | |
| `POST /api/matches/<id>/bracket-labels/` | `api_bracket_labels` | Superuser | |
| `POST /api/events/<id>/bracket/assign/` | `api_bracket_assign` | Superuser | |
| `POST /api/events/<id>/bracket/clear/` | `api_bracket_clear` | Superuser | |
| `GET /api/categories/` | `api_categories` | Superuser | Config, pas de vue TV |
| `GET /api/courts/` | `api_courts` | Superuser | Config, pas de vue TV |
| `POST /api/editions/create/` | `api_edition_create` | Superuser | |
| `POST /api/editions/<id>/edit/` | `api_edition_edit` | Superuser | |
| `POST /api/editions/<id>/activate/` | `api_edition_activate` | Superuser | |
| `POST /api/editions/<id>/delete/` | `api_edition_delete` | Superuser | |
| `POST /api/categories/create/` | `api_category_create` | Superuser | |
| `POST /api/categories/<id>/edit/` | `api_category_edit` | Superuser | |
| `POST /api/categories/<id>/delete/` | `api_category_delete` | Superuser | |
| `POST /api/courts/create/` | `api_court_create` | Superuser | |
| `POST /api/courts/<id>/edit/` | `api_court_edit` | Superuser | |
| `POST /api/courts/<id>/delete/` | `api_court_delete` | Superuser | |
| `POST /api/editions/<id>/events/create/` | `api_event_create` | Superuser | |
| `POST /api/events/<id>/edit/` | `api_event_edit` | Superuser | |
| `POST /api/events/<id>/start/` | `api_event_start` | Superuser | |
| `POST /api/events/<id>/close/` | `api_event_close` | Superuser | |
| `POST /api/events/<id>/reopen/` | `api_event_reopen` | Superuser | |
| `POST /api/events/<id>/delete/` | `api_event_delete` | Superuser | |
| `GET /api/editions/<id>/play-days/` | `api_play_days_list` | Superuser | |
| `POST /api/editions/<id>/play-days/create/` | `api_play_day_create` | Superuser | |
| `POST /api/play-days/<id>/edit/` | `api_play_day_edit` | Superuser | |
| `POST /api/play-days/<id>/delete/` | `api_play_day_delete` | Superuser | |
| `GET /api/play-days/<id>/breaks/` | `api_breaks_list` | Superuser | |
| `POST /api/play-days/<id>/breaks/create/` | `api_break_create` | Superuser | |
| `POST /api/breaks/<id>/edit/` | `api_break_edit` | Superuser | |
| `POST /api/breaks/<id>/delete/` | `api_break_delete` | Superuser | |
| `GET /api/editions/<id>/calendar/` | `api_edition_calendar` | Superuser | |
| `POST /api/editions/<id>/calendar/reorder/` | `api_calendar_reorder` | Superuser | |
| `POST /api/events/<id>/matches/auto-arrange/` | `api_matches_auto_arrange` | Superuser | |
| `GET /api/tv/upcoming/` | `api_tv_upcoming` | Public | Lecture TV |
| `POST /api/entries/<id>/withdraw/` | `api_entry_withdraw` | Superuser | |
| `POST /api/events/<id>/entries/add-late/` | `api_entry_add_late` | Superuser | |
| `POST /api/entries/<id>/replace/` | `api_entry_replace` | Superuser | |

## Incohérence corrigée par ce ticket

`api_players` et `api_player_create` étaient en `@login_required` (accessibles à
tout utilisateur connecté, y compris Arbitre) alors que `api_player_edit` — sur le
même objet `Player` — est en `@superuser_required`. Le registre de joueurs est un
écran admin only (`AdminPlayers.vue`, aucune consommation depuis
`frontend/app/src/views/arbitre/`). Les deux vues sont alignées sur
`@superuser_required` pour cohérence avec le reste des endpoints de gestion du
registre/inscriptions.

## Hors périmètre

- `api_logout` et `api_me` restent volontairement sans garde stricte (symétrie
  auth, contrat documenté dans [[erreurs-api]]).
- Les endpoints de lecture publics (TV) ne sont pas remis en cause par ce ticket :
  le choix « public » est nécessaire à l'écran spectateur et documenté ici comme
  décision assumée, pas comme oubli.

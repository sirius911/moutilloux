"""
API JSON — endpoints pour la SPA Vue.js.
Lectures en GET ; mutations en POST (JSON), par-dessus les fonctions de service
extraites de admin_views (aucune logique métier dupliquée ici).
"""
import json
from datetime import datetime, time

from django.http import JsonResponse
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date, parse_time

from core.models import get_current_edition, TournamentEdition, Player, Team
from competition.models import Category, Event, Entry, Group, GroupStanding, GroupMembership
from live.models import Match, Court, PlayDay, Break
from live.views import build_event_group_tables
from live.admin_views import (
    superuser_required,
    PlayerForm,
    MatchEditForm,
    create_team_with_entry,
    add_player_entry,
    add_players_entries,
    remove_entry,
    create_group,
    autofill_groups,
    generate_group_matches_for_event,
    assign_entry_to_group,
    unassign_entry,
    finalize_match_edit,
    feature_match,
    start_match,
    set_match_bracket_labels,
    assign_bracket_entry,
    clear_bracket_entry,
    # Phase 9 — services de configuration (éditions, catégories, courts, épreuves)
    create_edition,
    update_edition,
    set_active_edition,
    delete_edition,
    create_category,
    update_category,
    delete_category,
    create_court,
    update_court,
    delete_court,
    create_event,
    update_event,
    delete_event,
    # Sprint 11 — cycle de vie
    start_event,
    close_event,
    reopen_event,
    # Sprint 12 — ajustements en cours de jeu
    withdraw_entry,
    add_late_entry,
    replace_entry_player,
    # Sprint 07 — calendrier (journées + pauses)
    create_play_day,
    update_play_day,
    delete_play_day,
    create_break,
    update_break,
    delete_break,
    reorder_calendar,
    auto_arrange_matches,
)
from live.referee_views import referee_required


# ── CSRF ─────────────────────────────────────────────────────────────────────

@require_GET
@ensure_csrf_cookie
def api_csrf(request):
    """Pose le cookie csrftoken sans exiger d'authentification."""
    return JsonResponse({"detail": "ok"})


@require_POST
@csrf_protect
def api_logout(request):
    """POST /api/auth/logout/ — Déconnexion JSON (symétrique à api_login)."""
    auth_logout(request)
    return JsonResponse({"ok": True})


@require_POST
@csrf_protect
def api_login(request):
    """Authentification JSON pour la SPA Vue. Retourne le rôle de l'utilisateur."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"error": "Identifiants incorrects."}, status=401)

    login(request, user)
    return JsonResponse({
        "ok": True,
        "isAdmin": user.is_superuser,
        "isReferee": user.groups.filter(name="Arbitre").exists(),
    })


# ── Helpers ──────────────────────────────────────────────────────────────────

def _entry_display_name(entry):
    if entry is None:
        return None
    if entry.player:
        p = entry.player
        return f"{p.last_name} {p.first_name}".strip()
    if entry.team:
        t = entry.team
        return t.name or f"{t.player1} / {t.player2}"
    return str(entry)


def _pack_entry(entry):
    if entry is None:
        return None
    result = {
        "id": entry.id,
        "displayName": _entry_display_name(entry),
        "seedHint": entry.seed_hint,
        "groupId": None,
        "groupName": None,
        "withdrawn": entry.withdrawn,
    }
    # Groupe assigné (via GroupMembership)
    membership = getattr(entry, "_membership_cache", None)
    if membership:
        result["groupId"] = membership.group_id
        result["groupName"] = membership.group.name
    if entry.player:
        p = entry.player
        result["player"] = {
            "id": p.id,
            "firstName": p.first_name,
            "lastName": p.last_name,
            "fullName": str(p),
            "gender": p.gender,
            "licenseNumber": p.license_number,
        }
    else:
        result["player"] = None
    return result


def _pack_player(p):
    if p is None:
        return None
    return {
        "id": p.id,
        "firstName": p.first_name,
        "lastName": p.last_name,
        "fullName": str(p),
        "gender": p.gender,
        "birthYear": p.birth_year,
        "phone": p.phone,
        "email": p.email,
        "licenseNumber": p.license_number,
    }


def _pack_team(t):
    if t is None:
        return None
    return {
        "id": t.id,
        "name": t.name,
        "displayName": str(t),
        "player1": _pack_player(t.player1),
        "player2": _pack_player(t.player2),
    }


def _format_label(m):
    if m.match_format == Match.Format.MANUAL:
        return "Manuel"
    if m.best_of == 3:
        return f"BO3 · TB à {m.tb_at}"
    return f"1 set à {m.games_to_win} · TB à {m.tb_at}"


def _pack_match(m):
    if m is None:
        return None

    if m.tb_active:
        display_point_a = str(m.tb_points_a)
        display_point_b = str(m.tb_points_b)
    else:
        pa, pb = m.tennis_point_display()
        display_point_a, display_point_b = pa, pb

    from django.utils import timezone
    clock = None
    if m.started_at:
        delta = timezone.now() - m.started_at
        s = int(delta.total_seconds())
        clock = f"{s // 60:02d}:{s % 60:02d}"

    scheduled_str = None
    if m.scheduled_time:
        scheduled_str = timezone.localtime(m.scheduled_time).strftime("%Hh%M")

    def stage_label(match):
        labels = {
            Match.Stage.GROUP: "Match de poule",
            Match.Stage.QF: "Quart de finale",
            Match.Stage.SF: "Demi-finale",
            Match.Stage.F: "Finale",
            Match.Stage.P3: "3e place",
        }
        if match.stage == Match.Stage.GROUP and match.group:
            return f"Match de poule — Poule {match.group.name}"
        return labels.get(match.stage, match.stage)

    return {
        "id": m.id,
        "eventId": m.event_id,
        "stage": m.stage,
        "stageLabel": stage_label(m),
        "formatLabel": _format_label(m),
        "status": m.status,
        "court": m.court.name if m.court else None,
        "orderIndex": m.order_index,
        "isFeatured": m.is_featured,
        "bracketSlot": m.bracket_slot,
        "sideA": _pack_entry(m.side_a) if m.side_a else None,
        "sideB": _pack_entry(m.side_b) if m.side_b else None,
        "sideALabel": m.side_a_label,
        "sideBLabel": m.side_b_label,
        "server": m.server,
        "matchFormat": m.match_format,
        "bestOf": m.best_of,
        "gamesToWin": m.games_to_win,
        "tbAt": m.tb_at,
        "tbPointsToWin": m.tb_points_to_win,
        "tbWinByTwo": m.tb_win_by_two,
        "decidingSetMode": m.deciding_set_mode,
        "decidingTbPointsToWin": m.deciding_tb_points_to_win,
        "setsA": m.sets_a,
        "setsB": m.sets_b,
        "gamesA": m.games_a,
        "gamesB": m.games_b,
        "pointsA": m.points_a,
        "pointsB": m.points_b,
        "tbActive": m.tb_active,
        "tbPointsA": m.tb_points_a,
        "tbPointsB": m.tb_points_b,
        "setScores": m.set_scores or [],
        "displayPointA": display_point_a,
        "displayPointB": display_point_b,
        "winnerSide": m.winner_side,
        "isWalkover": m.is_walkover,
        "scheduledTime": scheduled_str,
        "startedAt": m.started_at.isoformat() if m.started_at else None,
        "finishedAt": m.finished_at.isoformat() if m.finished_at else None,
        "updatedAt": m.updated_at.isoformat(),
        "clock": clock,
    }


# ── Packers Phase 9 (config : éditions, catégories, courts, épreuves) ───────────

def _iso_or_none(dt):
    return dt.isoformat() if dt else None


def _pack_edition(edition):
    """Édition pour l'historique admin (Phase 9).
    Inclut les agrégats sprint-02 : joueurs distincts, matchs terminés/total.
    """
    events_qs = Event.objects.filter(edition=edition)
    events_count = events_qs.count()

    # Joueurs distincts inscrits à au moins une épreuve de l'édition
    # (les deux membres d'une équipe comptent chacun — spec admin-tournoi.md)
    player_ids: set[int] = set()
    for entry in (
        Entry.objects.filter(event__in=events_qs)
        .select_related("player", "team__player1", "team__player2")
    ):
        if entry.player_id:
            player_ids.add(entry.player_id)
        elif entry.team:
            if entry.team.player1_id:
                player_ids.add(entry.team.player1_id)
            if entry.team.player2_id:
                player_ids.add(entry.team.player2_id)

    # Matchs terminés / total (toutes épreuves de l'édition)
    matches_qs = Match.objects.filter(event__in=events_qs)
    matches_total = matches_qs.count()
    matches_finished = matches_qs.filter(status=Match.Status.FINISHED).count()

    return {
        "id": edition.id,
        "name": edition.name,
        "year": edition.year,
        "isActive": edition.is_active,
        "startDt": _iso_or_none(edition.start_dt),
        "endDt": _iso_or_none(edition.end_dt),
        "eventsCount": events_count,
        "distinctPlayersCount": len(player_ids),
        "matchesFinished": matches_finished,
        "matchesTotal": matches_total,
        "defaultMatchDurationMin": edition.default_match_duration_min,
    }


def _pack_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "mode": category.mode,
        "eventsCount": Event.objects.filter(category=category).count(),
    }


def _pack_court(court):
    return {
        "id": court.id,
        "name": court.name,
        "matchCount": Match.objects.filter(court=court).count(),
    }


def _pack_event(event):
    """Épreuve enrichie (Phase 9). Conserve id/editionId/name/categoryMode pour
    la compat front, ajoute la config par année + des indicateurs d'état."""
    return {
        "id": event.id,
        "editionId": event.edition_id,
        "name": str(event.category),
        "categoryId": event.category_id,
        "categoryMode": event.category.mode,
        "groupSizeDefault": event.group_size_default,
        "qualifiedPerGroup": event.qualified_per_group,
        "notes": event.notes,
        "hasThirdPlace": event.has_third_place,
        "status": event.status,
        "entriesCount": Entry.objects.filter(event=event).count(),
        "hasGroups": Group.objects.filter(event=event).exists(),
        "hasBracket": Match.objects.filter(
            event=event, stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F]
        ).exists(),
        "hasBracketStarted": Match.objects.filter(
            event=event,
            stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
            status__in=[Match.Status.LIVE, Match.Status.FINISHED],
        ).exists(),
    }


def _parse_edition_dt(value, label):
    """JSON → datetime aware | None. Accepte ISO 8601 ou « AAAA-MM-JJ ». '' / None → None."""
    if value in (None, ""):
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        d = parse_date(value)
        if d is not None:
            parsed = datetime.combine(d, time.min)
    if parsed is None:
        raise ValueError(f"{label} : date invalide (attendu AAAA-MM-JJ ou ISO 8601).")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


# ── Endpoints ─────────────────────────────────────────────────────────────────

@require_GET
def api_editions(request):
    """
    GET /api/editions/
    - activeEdition : édition courante (ou null)
    - events : épreuves de l'édition courante (packer enrichi Phase 9)
    - editions : historique complet (Phase 9) — alimente le tableau admin
    """
    edition = get_current_edition()
    editions = [_pack_edition(e) for e in TournamentEdition.objects.all()]

    if not edition:
        return JsonResponse({"activeEdition": None, "events": [], "editions": editions})

    events = (
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("category__name")
    )

    return JsonResponse({
        "activeEdition": _pack_edition(edition),
        "events": [_pack_event(ev) for ev in events],
        "editions": editions,
    })


@require_GET
def api_event_players(request, event_id):
    """
    GET /api/events/<id>/players/
    Liste des entries (joueurs/équipes) inscrites à l'épreuve.
    """
    event = get_object_or_404(Event, pk=event_id)

    entries = (
        event.entries
        .select_related("player", "team", "team__player1", "team__player2")
        .prefetch_related("group_memberships__group")
        .order_by("player__last_name", "player__first_name", "id")
    )

    result = []
    for entry in entries:
        membership = entry.group_memberships.first()
        if membership:
            entry._membership_cache = membership
        data = _pack_entry(entry)
        if membership:
            data["groupId"] = membership.group_id
            data["groupName"] = membership.group.name
        result.append(data)

    return JsonResponse(result, safe=False)


@require_GET
def api_event_groups(request, event_id):
    """
    GET /api/events/<id>/groups/
    Groupes avec standings et grille croisée.
    """
    event = get_object_or_404(Event, pk=event_id)
    edition = event.edition

    tables = build_event_group_tables(edition, [event])
    groups_data = tables.get(event.id, [])

    result = []
    for table in groups_data:
        group = table["group"]
        entries = table["entries"]
        standing_by = table["standing_by_entry_id"]
        cell = table["cell"]
        match_cols = table["match_cols"]
        qualif = table["qualif"]

        # Standings
        standings = []
        for i, entry in enumerate(entries):
            s = standing_by.get(entry.id)
            if s:
                games_won = s.games_won
                games_lost = s.games_lost
                wins = s.wins
                losses = s.losses
                points = s.points
                rank = s.rank or (i + 1)
            else:
                games_won = games_lost = wins = losses = points = 0
                rank = i + 1

            standings.append({
                "entryId": entry.id,
                "rank": rank,
                "name": _entry_display_name(entry),
                "wins": wins,
                "losses": losses,
                "gamesRatio": f"{games_won}/{games_lost}",
                "points": points,
                "qualified": qualif.get(entry.id, "-") != "-",
                "withdrawn": entry.withdrawn,
            })

        # Grille croisée (matrice n×n)
        # On cherche pour chaque paire (row, col) le score du match
        n = len(entries)
        grid = []
        for ri in range(n):
            row_cells = []
            for ci in range(n):
                if ri == ci:
                    row_cells.append({"score": None})
                else:
                    # Trouver le match entre entries[ri] et entries[ci]
                    row_entry = entries[ri]
                    col_entry = entries[ci]
                    score = None
                    for m in match_cols:
                        if m.status == Match.Status.FINISHED:
                            if m.side_a_id == row_entry.id and m.side_b_id == col_entry.id:
                                score = f"{m.games_a}-{m.games_b}"
                                break
                            elif m.side_a_id == col_entry.id and m.side_b_id == row_entry.id:
                                score = f"{m.games_b}-{m.games_a}"
                                break
                    row_cells.append({"score": score})
            grid.append(row_cells)

        result.append({
            "id": group.id,
            "name": group.name,
            "standings": standings,
            "grid": grid,
        })

    locked = event.status != Event.Status.INSCRIPTION
    return JsonResponse({"locked": locked, "groups": result})


@require_GET
def api_event_matches(request, event_id):
    """
    GET /api/events/<id>/matches/
    Matchs groupés en backlog / queue / finished pour le kanban admin.
    """
    event = get_object_or_404(Event, pk=event_id)

    qs = (
        Match.objects.filter(event=event)
        .select_related("court", "side_a", "side_a__player", "side_b", "side_b__player", "group")
        .order_by("order_index", "scheduled_time", "id")
    )

    backlog = []
    queue = []
    finished = []

    for m in qs:
        packed = _pack_match(m)
        if m.status == Match.Status.FINISHED:
            finished.append(packed)
        elif m.status == Match.Status.SCHEDULED and m.order_index is not None:
            queue.append(packed)
        elif m.status in (Match.Status.SCHEDULED, Match.Status.LIVE):
            backlog.append(packed)

    return JsonResponse({"backlog": backlog, "queue": queue, "finished": finished})


@require_GET
def api_match_detail(request, match_id):
    """
    GET /api/matches/<id>/
    État d'un match unique (polling arbitre + scoreboard). Réexpose _pack_match.
    Lecture publique (cohérent avec les autres GET de match ; utilisé par la TV).
    """
    match = get_object_or_404(
        Match.objects.select_related(
            "court", "side_a", "side_a__player", "side_b", "side_b__player", "group"
        ),
        pk=match_id,
    )
    return JsonResponse({"match": _pack_match(match)})


def _pack_event_bracket(event):
    """Structure du tableau final (QF/SF/F/P3) groupée par slot — format partagé."""
    qs = (
        Match.objects.filter(
            event=event,
            stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
        )
        .select_related("court", "side_a", "side_a__player", "side_b", "side_b__player")
        .order_by("bracket_slot")
    )

    def make_slot(stage, slot_key, match):
        return {
            "slot": slot_key,
            "stage": stage,
            "match": _pack_match(match) if match else None,
        }

    by_slot = {m.bracket_slot: m for m in qs if m.bracket_slot}

    return {
        "qf": [make_slot("QF", k, by_slot.get(k)) for k in ("QF1", "QF2", "QF3", "QF4")],
        "sf": [make_slot("SF", k, by_slot.get(k)) for k in ("SF1", "SF2")],
        "f": [make_slot("F", k, by_slot.get(k)) for k in ("F1",)],
        "p3": [make_slot("P3", "P3", by_slot.get("P3"))],
    }


@require_GET
def api_event_bracket(request, event_id):
    """
    GET /api/events/<id>/bracket/
    Données du tableau final (QF, SF, Finale).
    """
    event = get_object_or_404(Event, pk=event_id)
    return JsonResponse(_pack_event_bracket(event))


@require_GET
@referee_required
def api_arbitre_matches(request):
    """
    GET /api/arbitre/matches/
    Matchs LIVE et SCHEDULED pour l'arbitre (sélection de match).
    Requiert le rôle Arbitre (ou superuser).
    """
    edition = get_current_edition()
    if not edition:
        return JsonResponse([], safe=False)

    # Matchs actifs (LIVE + SCHEDULED) — ordre existant préservé
    active_qs = (
        Match.objects.filter(
            edition=edition,
            status__in=[Match.Status.LIVE, Match.Status.SCHEDULED],
        )
        .select_related("court", "side_a", "side_a__player", "side_b", "side_b__player", "event", "group")
        .order_by("order_index", "scheduled_time", "id")
    )

    # 20 derniers FINISHED
    finished_qs = (
        Match.objects.filter(
            edition=edition,
            status=Match.Status.FINISHED,
        )
        .select_related("court", "side_a", "side_a__player", "side_b", "side_b__player", "event", "group")
        .order_by("-id")[:20]
    )

    matches = list(active_qs) + list(finished_qs)
    return JsonResponse([_pack_match(m) for m in matches], safe=False)


@require_GET
@superuser_required
def api_players(request):
    """
    GET /api/players/
    Retourne tous les joueurs du registre global. Requiert le rôle superuser (admin).
    """
    players = Player.objects.all().order_by("last_name", "first_name")
    return JsonResponse([_pack_player(p) for p in players], safe=False)


@require_POST
@superuser_required
def api_player_create(request):
    """
    POST /api/players/create/
    Crée un joueur dans le registre global. Requiert le rôle superuser (admin).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    gender = data.get("gender", "")
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    license_number = data.get("license_number", "").strip()

    if not first_name or not last_name:
        return JsonResponse({"error": "Prénom et nom requis."}, status=400)

    birth_year_raw = data.get("birth_year")
    birth_year = None
    if birth_year_raw is not None:
        try:
            y = int(birth_year_raw)
            if 1900 <= y <= 2100:
                birth_year = y
        except (ValueError, TypeError):
            pass

    player = Player.objects.create(
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        birth_year=birth_year,
        email=email,
        phone=phone,
        license_number=license_number,
    )

    return JsonResponse({"ok": True, "playerId": player.id})


@require_GET
def api_me(request):
    """
    GET /api/me/
    Retourne l'utilisateur courant (ou 401 si non connecté).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not authenticated"}, status=401)

    return JsonResponse({
        "id": request.user.id,
        "username": request.user.username,
        "isSuperuser": request.user.is_superuser,
        "isReferee": request.user.groups.filter(name="Arbitre").exists(),
    })


# ── Phase 2 — Inscriptions (mutations) ─────────────────────────────────────────

@require_POST
@superuser_required
def api_player_edit(request, player_id):
    """
    POST /api/players/<id>/edit/
    Édite un joueur du registre via PlayerForm (source : admin_views.player_edit).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    player = get_object_or_404(Player, pk=player_id)

    # Fusion partielle : on part des valeurs actuelles du joueur et on n'écrase
    # que les champs réellement fournis. Évite de vider phone/email/license quand
    # la modale n'envoie que nom/prénom/genre.
    fields = PlayerForm.Meta.fields
    merged = {f: getattr(player, f) for f in fields}
    merged.update({k: v for k, v in data.items() if k in fields})

    form = PlayerForm(merged, instance=player)
    if not form.is_valid():
        return JsonResponse({"error": "Données invalides", "fields": form.errors}, status=400)

    form.save()
    return JsonResponse({"player": _pack_player(player)})


@require_POST
@superuser_required
def api_team_create(request, event_id):
    """
    POST /api/events/<id>/teams/create/
    Crée une équipe (double) + Entry (source : admin_views.team_create).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event.objects.select_related("category"), pk=event_id)

    player1 = Player.objects.filter(pk=data.get("player1")).first()
    player2 = Player.objects.filter(pk=data.get("player2")).first()
    if player1 is None or player2 is None:
        return JsonResponse({"error": "player1 et player2 sont requis (IDs de joueurs)."}, status=400)

    try:
        team, entry = create_team_with_entry(event, player1, player2, data.get("name", ""))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"team": _pack_team(team), "entry": _pack_entry(entry)})


@require_POST
@superuser_required
def api_registration_add(request, event_id):
    """
    POST /api/events/<id>/registrations/add/
    Inscrit un joueur (simple) via une Entry (source : admin_views.entry_add_player).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event.objects.select_related("category"), pk=event_id)

    player = Player.objects.filter(pk=data.get("player")).first()
    if player is None:
        return JsonResponse({"error": "player requis (ID de joueur)."}, status=400)

    try:
        entry = add_player_entry(event, player)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"entry": _pack_entry(entry)})


@require_POST
@superuser_required
def api_registration_add_bulk(request, event_id):
    """
    POST /api/events/<id>/registrations/add-bulk/
    Inscrit plusieurs joueurs (simple) (source : admin_views.entry_add_players).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    raw_ids = data.get("player_ids") or []
    try:
        player_ids = [int(x) for x in raw_ids]
    except (ValueError, TypeError):
        return JsonResponse({"error": "player_ids doit être une liste d'entiers."}, status=400)

    event = get_object_or_404(Event.objects.select_related("category"), pk=event_id)

    try:
        created, skipped = add_players_entries(event, player_ids)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "created": [_pack_entry(e) for e in created],
        "skipped": skipped,
    })


@require_POST
@superuser_required
def api_registration_remove(request, event_id, entry_id):
    """
    POST /api/events/<id>/registrations/<entry_id>/remove/
    Retire une Entry (source : admin_views.entry_remove).
    Refuse si l'Entry est engagée dans un match.
    """
    event = get_object_or_404(Event, pk=event_id)
    entry = get_object_or_404(Entry, pk=entry_id, event=event)

    try:
        remove_entry(event, entry)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=409)

    return JsonResponse({"ok": True})


# ── Phase 3 — Poules (mutations) ───────────────────────────────────────────────

@require_POST
@superuser_required
def api_group_create(request, event_id):
    """
    POST /api/events/<id>/groups/create/
    Crée une poule (source : admin_views.create_group). Body JSON: {name}.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    try:
        group, _ = create_group(event, data.get("name", ""))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"group": {"id": group.id, "name": group.name}})


@require_POST
@superuser_required
@transaction.atomic
def api_groups_autofill(request, event_id):
    """
    POST /api/events/<id>/groups/autofill/
    Réinitialise et répartit les inscrits en round-robin
    (source : admin_views.autofill_groups). Body JSON: {shuffle, group_size, num_groups?}.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    group_size = data.get("group_size", 4)
    if int(group_size) not in (3, 4):
        return JsonResponse({"error": "group_size doit valoir 3 ou 4."}, status=400)

    try:
        groups = autofill_groups(
            event,
            shuffle=bool(data.get("shuffle", False)),
            group_size=group_size,
            num_groups=data.get("num_groups"),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "groups": [{"id": g.id, "name": g.name} for g in groups],
    })


@require_POST
@superuser_required
@transaction.atomic
def api_matches_generate(request, event_id):
    """
    POST /api/events/<id>/matches/generate/
    Génère le round-robin de chaque poule (source : admin_views.generate_group_matches_for_event).
    Aucun paramètre ; idempotent ; format par défaut G_SET5_TB44.
    """
    event = get_object_or_404(Event, pk=event_id)
    created, matches = generate_group_matches_for_event(event)
    return JsonResponse({
        "created": created,
        "matches": [_pack_match(m) for m in matches],
    })


@require_POST
@superuser_required
@transaction.atomic
def api_group_assign(request, event_id):
    """
    POST /api/events/<id>/groups/assign/
    Assigne/déplace une Entry dans une poule (source : admin_views.assign_entry_to_group).
    Body JSON: {entry_id, group_id}. Verrouillé si status != INSCRIPTION.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    entry_id = data.get("entry_id")
    group_id = data.get("group_id")
    if not entry_id or not group_id:
        return JsonResponse({"error": "entry_id et group_id sont requis."}, status=400)

    entry = get_object_or_404(Entry, pk=entry_id, event=event)
    group = get_object_or_404(Group, pk=group_id, event=event)

    try:
        assign_entry_to_group(event, entry, group)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


@require_POST
@superuser_required
@transaction.atomic
def api_group_unassign(request, event_id):
    """
    POST /api/events/<id>/groups/unassign/
    Retire une Entry de sa poule (source : admin_views.unassign_entry).
    Body JSON: {entry_id}. Verrouillé si status != INSCRIPTION.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    entry_id = data.get("entry_id")
    if not entry_id:
        return JsonResponse({"error": "entry_id est requis."}, status=400)

    entry = get_object_or_404(Entry, pk=entry_id, event=event)

    try:
        unassign_entry(event, entry)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


# ── Phase 4 — Planning (mutations) ─────────────────────────────────────────────

@require_POST
@superuser_required
def api_match_edit(request, match_id):
    """
    POST /api/matches/<id>/edit/
    Édite un match via MatchEditForm (source : admin_views.match_edit).
    Fusion partielle : on part des valeurs actuelles puis on n'écrase que les
    champs fournis. Les champs verrouillés par le form (format quand LIVE,
    order_index) sont ignorés côté form → la règle de verrouillage est conservée.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    match = get_object_or_404(Match, pk=match_id)
    was_live = match.status == Match.Status.LIVE
    was_finished = match.status == Match.Status.FINISHED

    fields = MatchEditForm.Meta.fields
    merged = {}
    for f in fields:
        merged[f] = getattr(match, f)
    for k, v in data.items():
        if k in fields:
            merged[k] = v

    form = MatchEditForm(merged, instance=match)
    if not form.is_valid():
        return JsonResponse({"error": "Données invalides", "fields": form.errors}, status=400)

    try:
        form.save()
        finalize_match_edit(form.instance, was_live=was_live, was_finished=was_finished)
    except IntegrityError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"match": _pack_match(form.instance)})


@require_POST
@superuser_required
@transaction.atomic
def api_match_feature(request, match_id):
    """
    POST /api/matches/<id>/feature/
    Met le match en avant (source : admin_views.feature_match). Aucun payload.
    Effet : is_featured=True, mark_live() → statut LIVE ; order_index inchangé ;
    devient le hero de /api/score_state/.
    """
    match = get_object_or_404(Match, pk=match_id)
    feature_match(match)
    return JsonResponse({"match": _pack_match(match)})


@require_POST
@superuser_required
@transaction.atomic
def api_match_start(request, match_id):
    """
    POST /api/matches/<id>/start/
    Démarre le match (SCHEDULED -> LIVE), le met en avant TV (source :
    admin_views.start_match — service partagé avec referee_action('start')).
    Idempotent : si déjà LIVE, no-op ; répond quand même 200 avec le match packé.
    Aucun payload attendu.
    """
    match = get_object_or_404(Match, pk=match_id)
    try:
        start_match(match)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"match": _pack_match(match)})


# ── Phase 7 — Bracket (mutations) ───────────────────────────────────────────────
@require_POST
@superuser_required
@transaction.atomic
def api_bracket_create(request, event_id):
    """
    POST /api/events/<id>/bracket/create/
    Crée ou (re)crée le squelette du tableau final (générateur général : N poules × qpg, byes,
    séparation maximale — source : live.bracket.recreate_final_bracket_for_event).
    Body JSON optionnel : {force: bool} (défaut false).
    - Sans tableau existant : le squelette est créé (force sans effet).
    - Tableau existant, force=false : idempotent, rien n'est effacé.
    - Tableau existant, force=true : les matchs planifiés (SCHEDULED) sont effacés puis
      le squelette est reposé.
    - Refusé (400) si un match du tableau est déjà LIVE/FINISHED, que force soit vrai ou non.
    Réponse : structure du bracket (même format que GET /api/events/<id>/bracket/).
    """
    event = get_object_or_404(Event.objects.select_related("edition"), pk=event_id)

    try:
        data = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    force = bool(data.get("force", False))

    from live.bracket import recreate_final_bracket_for_event
    try:
        recreate_final_bracket_for_event(event, force=force)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(_pack_event_bracket(event))


@require_POST
@superuser_required
def api_bracket_labels(request, match_id):
    """
    POST /api/matches/<id>/bracket-labels/
    Met à jour les labels d'un match du tableau final (source : admin_views.set_match_bracket_labels).
    Body JSON : {side_a_label, side_b_label}. Refusé (400) si le match n'est plus SCHEDULED.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    match = get_object_or_404(
        Match,
        pk=match_id,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
    )

    try:
        set_match_bracket_labels(match, data.get("side_a_label"), data.get("side_b_label"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"match": _pack_match(match)})



@require_POST
@superuser_required
@transaction.atomic
def api_bracket_assign(request, event_id):
    """
    POST /api/events/<id>/bracket/assign/
    Assigne une Entry à un côté d'un match de tableau final
    (source : admin_views.assign_bracket_entry).
    Body JSON : {match_id, entry_id, side}.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    match_id = data.get("match_id")
    entry_id = data.get("entry_id")
    side = (data.get("side") or "").upper()

    if not match_id or not entry_id or side not in {"A", "B"}:
        return JsonResponse({"error": "match_id, entry_id et side sont requis."}, status=400)

    try:
        assign_bracket_entry(event, int(match_id), int(entry_id), side)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


@require_POST
@superuser_required
@transaction.atomic
def api_bracket_clear(request, event_id):
    """
    POST /api/events/<id>/bracket/clear/
    Retire l'Entry d'un côté d'un match de tableau final
    (source : admin_views.clear_bracket_entry).
    Body JSON : {match_id, side}.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    event = get_object_or_404(Event, pk=event_id)

    match_id = data.get("match_id")
    side = (data.get("side") or "").upper()

    if not match_id or side not in {"A", "B"}:
        return JsonResponse({"error": "match_id et side sont requis."}, status=400)

    try:
        clear_bracket_entry(event, int(match_id), side)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9 — Administration de la configuration
# Lectures (catégories, courts) + mutations CRUD (éditions, catégories, courts,
# épreuves). Vues fines par-dessus les services de admin_views ; auth superuser,
# CSRF sur écritures. Les services lèvent ValueError → 400 ; doublons d'unicité
# pré-vérifiés côté service (message clair) plutôt que IntegrityError nue.
# ═══════════════════════════════════════════════════════════════════════════════

def _json_body(request):
    """Parse le corps JSON ('' → {}). Renvoie (data, None) ou (None, JsonResponse 400)."""
    if not request.body:
        return {}, None
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse({"error": "Corps JSON invalide"}, status=400)


# ── Lectures ────────────────────────────────────────────────────────────────

@require_GET
@superuser_required
def api_categories(request):
    """GET /api/categories/ — référentiel des catégories (toutes éditions)."""
    cats = Category.objects.all().order_by("name")
    return JsonResponse([_pack_category(c) for c in cats], safe=False)


@require_GET
@superuser_required
def api_courts(request):
    """GET /api/courts/ — terrains."""
    courts = Court.objects.all().order_by("name")
    return JsonResponse([_pack_court(c) for c in courts], safe=False)


# ── Éditions ──────────────────────────────────────────────────────────────────

@require_POST
@superuser_required
@transaction.atomic
def api_edition_create(request):
    """POST /api/editions/create/ — {name, year, start_dt?, end_dt?}."""
    data, err = _json_body(request)
    if err:
        return err
    try:
        edition = create_edition(
            name=data.get("name"),
            year=data.get("year"),
            start_dt=_parse_edition_dt(data.get("start_dt"), "Date de début"),
            end_dt=_parse_edition_dt(data.get("end_dt"), "Date de fin"),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_edition(edition))


@require_POST
@superuser_required
@transaction.atomic
def api_edition_edit(request, edition_id):
    """POST /api/editions/<id>/edit/ — {name?, year?, start_dt?, end_dt?, default_match_duration_min?} (édition partielle)."""
    data, err = _json_body(request)
    if err:
        return err
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    kwargs = {}
    if "name" in data:
        kwargs["name"] = data["name"]
    if "year" in data:
        kwargs["year"] = data["year"]
    if "default_match_duration_min" in data:
        val = data["default_match_duration_min"]
        try:
            kwargs["default_match_duration_min"] = max(1, int(val))
        except (TypeError, ValueError):
            return JsonResponse({"error": "default_match_duration_min doit être un entier positif"}, status=400)
    try:
        if "start_dt" in data:
            kwargs["start_dt"] = _parse_edition_dt(data["start_dt"], "Date de début")
        if "end_dt" in data:
            kwargs["end_dt"] = _parse_edition_dt(data["end_dt"], "Date de fin")
        update_edition(edition, **kwargs)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_edition(edition))


@require_POST
@superuser_required
@transaction.atomic
def api_edition_activate(request, edition_id):
    """POST /api/editions/<id>/activate/ — rend l'édition courante (désactive les autres)."""
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    set_active_edition(edition)
    return JsonResponse(_pack_edition(edition))


@require_POST
@superuser_required
@transaction.atomic
def api_edition_delete(request, edition_id):
    """POST /api/editions/<id>/delete/ — refusé (400) si l'édition contient des épreuves."""
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    try:
        delete_edition(edition)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True})


# ── Catégories ────────────────────────────────────────────────────────────────

@require_POST
@superuser_required
@transaction.atomic
def api_category_create(request):
    """POST /api/categories/create/ — {name, mode}."""
    data, err = _json_body(request)
    if err:
        return err
    try:
        category = create_category(name=data.get("name"), mode=data.get("mode"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_category(category))


@require_POST
@superuser_required
@transaction.atomic
def api_category_edit(request, category_id):
    """POST /api/categories/<id>/edit/ — {name?, mode?} (mode bloqué si inscriptions)."""
    data, err = _json_body(request)
    if err:
        return err
    category = get_object_or_404(Category, pk=category_id)
    kwargs = {}
    if "name" in data:
        kwargs["name"] = data["name"]
    if "mode" in data:
        kwargs["mode"] = data["mode"]
    try:
        update_category(category, **kwargs)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_category(category))


@require_POST
@superuser_required
@transaction.atomic
def api_category_delete(request, category_id):
    """POST /api/categories/<id>/delete/ — refusé (400, PROTECT) si une épreuve l'utilise."""
    category = get_object_or_404(Category, pk=category_id)
    try:
        delete_category(category)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True})


# ── Courts ──────────────────────────────────────────────────────────────────

@require_POST
@superuser_required
@transaction.atomic
def api_court_create(request):
    """POST /api/courts/create/ — {name}."""
    data, err = _json_body(request)
    if err:
        return err
    try:
        court = create_court(name=data.get("name"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_court(court))


@require_POST
@superuser_required
@transaction.atomic
def api_court_edit(request, court_id):
    """POST /api/courts/<id>/edit/ — {name}."""
    data, err = _json_body(request)
    if err:
        return err
    court = get_object_or_404(Court, pk=court_id)
    try:
        update_court(court, name=data.get("name"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_court(court))


@require_POST
@superuser_required
@transaction.atomic
def api_court_delete(request, court_id):
    """POST /api/courts/<id>/delete/ — refusé (400) si un match ordonné y est attaché."""
    court = get_object_or_404(Court, pk=court_id)
    try:
        delete_court(court)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True})


# ── Épreuves (Event = édition × catégorie) ──────────────────────────────────────

@require_POST
@superuser_required
@transaction.atomic
def api_event_create(request, edition_id):
    """POST /api/editions/<id>/events/create/ —
    {category_id, group_size_default?, qualified_per_group?, notes?}."""
    data, err = _json_body(request)
    if err:
        return err
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    category_id = data.get("category_id")
    if not category_id:
        return JsonResponse({"error": "category_id requis."}, status=400)
    category = get_object_or_404(Category, pk=category_id)
    try:
        event = create_event(
            edition,
            category,
            group_size_default=data.get("group_size_default", 4),
            qualified_per_group=data.get("qualified_per_group", 2),
            notes=data.get("notes", ""),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_event(event))


@require_POST
@superuser_required
@transaction.atomic
def api_event_edit(request, event_id):
    """POST /api/events/<id>/edit/ — {group_size_default?, qualified_per_group?, notes?, has_third_place?}."""
    data, err = _json_body(request)
    if err:
        return err
    event = get_object_or_404(Event.objects.select_related("category", "edition"), pk=event_id)
    kwargs = {}
    if "group_size_default" in data:
        kwargs["group_size_default"] = data["group_size_default"]
    if "qualified_per_group" in data:
        kwargs["qualified_per_group"] = data["qualified_per_group"]
    if "notes" in data:
        kwargs["notes"] = data["notes"]
    if "has_third_place" in data:
        kwargs["has_third_place"] = data["has_third_place"]
    try:
        update_event(event, **kwargs)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_event(event))


@require_POST
@superuser_required
def api_event_start(request, event_id):
    """POST /api/events/<id>/start/ — INSCRIPTION → EN_COURS.
    Réponse : {event, created, unplaced}."""
    event = get_object_or_404(Event.objects.select_related("category", "edition"), pk=event_id)
    try:
        result = start_event(event)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({
        "event": _pack_event(event),
        "created": result["created"],
        "unplaced": [_pack_entry(e) for e in result["unplaced"]],
    })


@require_POST
@superuser_required
def api_event_close(request, event_id):
    """POST /api/events/<id>/close/ — EN_COURS → TERMINEE (manuel admin).
    Réponse : {event}."""
    event = get_object_or_404(Event.objects.select_related("category", "edition"), pk=event_id)
    try:
        close_event(event)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"event": _pack_event(event)})


@require_POST
@superuser_required
def api_event_reopen(request, event_id):
    """POST /api/events/<id>/reopen/ — TERMINEE → EN_COURS (recours admin).
    Réponse : {event}."""
    event = get_object_or_404(Event.objects.select_related("category", "edition"), pk=event_id)
    try:
        reopen_event(event)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"event": _pack_event(event)})


@require_POST
@superuser_required
@transaction.atomic
def api_event_delete(request, event_id):
    """POST /api/events/<id>/delete/ — refusé (400) si des matchs sont LIVE/terminés."""
    event = get_object_or_404(Event, pk=event_id)
    try:
        delete_event(event)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True})


# ── Sprint 07 — Calendrier : PlayDay + Break ─────────────────────────────────

def _pack_play_day(pd):
    return {
        "id": pd.id,
        "editionId": pd.edition_id,
        "date": pd.date.isoformat(),
        "startTime": pd.start_time.strftime("%H:%M"),
        "targetEndTime": pd.target_end_time.strftime("%H:%M"),
    }


def _pack_break(brk):
    return {
        "id": brk.id,
        "playDayId": brk.play_day_id,
        "orderIndex": brk.order_index,
        "durationMin": brk.duration_min,
        "label": brk.label,
    }


@require_GET
@superuser_required
def api_play_days_list(request, edition_id):
    """GET /api/editions/<id>/play-days/"""
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    play_days = PlayDay.objects.filter(edition=edition).order_by("date")
    return JsonResponse({"playDays": [_pack_play_day(pd) for pd in play_days]})


@require_POST
@superuser_required
@transaction.atomic
def api_play_day_create(request, edition_id):
    """POST /api/editions/<id>/play-days/create/"""
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    date = parse_date(data.get("date", ""))
    start_time = parse_time(data.get("startTime", ""))
    target_end_time = parse_time(data.get("targetEndTime", ""))

    if not date or not start_time or not target_end_time:
        return JsonResponse({"error": "date, startTime et targetEndTime sont requis"}, status=400)

    try:
        pd = create_play_day(edition, date, start_time, target_end_time)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_play_day(pd), status=201)


@require_POST
@superuser_required
@transaction.atomic
def api_play_day_edit(request, play_day_id):
    """POST /api/play-days/<id>/edit/"""
    pd = get_object_or_404(PlayDay, pk=play_day_id)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    kwargs = {}
    if "date" in data:
        d = parse_date(data["date"])
        if not d:
            return JsonResponse({"error": "date invalide"}, status=400)
        kwargs["date"] = d
    if "startTime" in data:
        t = parse_time(data["startTime"])
        if not t:
            return JsonResponse({"error": "startTime invalide"}, status=400)
        kwargs["start_time"] = t
    if "targetEndTime" in data:
        t = parse_time(data["targetEndTime"])
        if not t:
            return JsonResponse({"error": "targetEndTime invalide"}, status=400)
        kwargs["target_end_time"] = t

    try:
        pd = update_play_day(pd, **kwargs)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_play_day(pd))


@require_POST
@superuser_required
@transaction.atomic
def api_play_day_delete(request, play_day_id):
    """POST /api/play-days/<id>/delete/"""
    pd = get_object_or_404(PlayDay, pk=play_day_id)
    try:
        delete_play_day(pd)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=409)
    return JsonResponse({"ok": True})


@require_GET
@superuser_required
def api_breaks_list(request, play_day_id):
    """GET /api/play-days/<id>/breaks/"""
    pd = get_object_or_404(PlayDay, pk=play_day_id)
    breaks = Break.objects.filter(play_day=pd).order_by("order_index")
    return JsonResponse({"breaks": [_pack_break(b) for b in breaks]})


@require_POST
@superuser_required
@transaction.atomic
def api_break_create(request, play_day_id):
    """POST /api/play-days/<id>/breaks/create/"""
    pd = get_object_or_404(PlayDay, pk=play_day_id)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    try:
        order_index = int(data.get("orderIndex", 0))
        duration_min = int(data.get("durationMin", 0))
    except (TypeError, ValueError):
        return JsonResponse({"error": "orderIndex et durationMin doivent être des entiers"}, status=400)

    label = data.get("label", "")

    try:
        brk = create_break(pd, order_index, duration_min, label)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_break(brk), status=201)


@require_POST
@superuser_required
@transaction.atomic
def api_break_edit(request, break_id):
    """POST /api/breaks/<id>/edit/"""
    brk = get_object_or_404(Break, pk=break_id)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    kwargs = {}
    if "orderIndex" in data:
        try:
            kwargs["order_index"] = int(data["orderIndex"])
        except (TypeError, ValueError):
            return JsonResponse({"error": "orderIndex doit être un entier"}, status=400)
    if "durationMin" in data:
        try:
            kwargs["duration_min"] = int(data["durationMin"])
        except (TypeError, ValueError):
            return JsonResponse({"error": "durationMin doit être un entier"}, status=400)
    if "label" in data:
        kwargs["label"] = data["label"]

    try:
        brk = update_break(brk, **kwargs)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(_pack_break(brk))


@require_POST
@superuser_required
@transaction.atomic
def api_break_delete(request, break_id):
    """POST /api/breaks/<id>/delete/"""
    brk = get_object_or_404(Break, pk=break_id)
    delete_break(brk)
    return JsonResponse({"ok": True})


# ── Sprint 07 — Packer calendrier ────────────────────────────────────────────

@require_GET
@superuser_required
def api_edition_calendar(request, edition_id):
    """
    GET /api/editions/<id>/calendar/
    Retourne les journées avec leurs matchs ordonnés + la pile des matchs
    à planifier (SCHEDULED, sans order_index, poules uniquement — MVP).
    """
    edition = get_object_or_404(TournamentEdition, pk=edition_id)

    play_days = list(
        PlayDay.objects.filter(edition=edition)
        .prefetch_related("breaks")
        .order_by("date")
    )

    # Matchs assignés à une journée : order_index non null ET scheduled_time non null
    assigned_matches = (
        Match.objects
        .filter(edition=edition, order_index__isnull=False, scheduled_time__isnull=False)
        .select_related("court", "group", "event",
                        "side_a__player", "side_a__team__player1", "side_a__team__player2",
                        "side_b__player", "side_b__team__player1", "side_b__team__player2")
        .order_by("order_index")
    )

    # Regrouper les matchs assignés par date (date locale du scheduled_time)
    from collections import defaultdict
    matches_by_date = defaultdict(list)
    for m in assigned_matches:
        day_key = timezone.localtime(m.scheduled_time).date()
        matches_by_date[day_key].append(m)

    packed_play_days = []
    for pd in play_days:
        packed_play_days.append({
            **_pack_play_day(pd),
            "breaks": [_pack_break(b) for b in sorted(pd.breaks.all(), key=lambda b: b.order_index)],
            "matches": [_pack_match(m) for m in matches_by_date.get(pd.date, [])],
        })

    # Pile à planifier : SCHEDULED, order_index IS NULL, poules uniquement (MVP)
    unscheduled = (
        Match.objects
        .filter(edition=edition, status=Match.Status.SCHEDULED,
                order_index__isnull=True, stage=Match.Stage.GROUP)
        .select_related("court", "group", "event",
                        "side_a__player", "side_a__team__player1", "side_a__team__player2",
                        "side_b__player", "side_b__team__player1", "side_b__team__player2")
        .order_by("event_id", "id")
    )

    # Matchs annulés (quittent la séquence, poules uniquement — cohérent avec unscheduled)
    canceled = (
        Match.objects
        .filter(edition=edition, status=Match.Status.CANCELED, stage=Match.Stage.GROUP)
        .select_related("court", "group", "event",
                        "side_a__player", "side_a__team__player1", "side_a__team__player2",
                        "side_b__player", "side_b__team__player1", "side_b__team__player2")
        .order_by("event_id", "id")
    )

    return JsonResponse({
        "playDays": packed_play_days,
        "unscheduled": [_pack_match(m) for m in unscheduled],
        "canceled": [_pack_match(m) for m in canceled],
    })


@require_POST
@superuser_required
@transaction.atomic
def api_calendar_reorder(request, edition_id):
    """
    POST /api/editions/<id>/calendar/reorder/
    Réordonne le calendrier de l'édition.
    Body JSON : {"playDays": [{"playDayId": int, "items": [{"type": "match"|"break", "id": int}]}]}
    """
    edition = get_object_or_404(TournamentEdition, pk=edition_id)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps JSON invalide"}, status=400)

    play_day_sequences = data.get("playDays", [])
    if not isinstance(play_day_sequences, list):
        return JsonResponse({"error": "playDays doit être une liste"}, status=400)

    try:
        reorder_calendar(edition, play_day_sequences)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


@require_POST
@superuser_required
@transaction.atomic
def api_matches_auto_arrange(request, event_id):
    """
    POST /api/events/<id>/matches/auto-arrange/
    Pré-pose les matchs à planifier (SCHEDULED + GROUP + sans order_index) sur les journées.
    Réponse : {"placed": N}
    """
    event = get_object_or_404(Event, pk=event_id)
    try:
        placed = auto_arrange_matches(event.edition)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"placed": placed})


# ── Sprint 07 — TV : prochains matchs ────────────────────────────────────────

def get_tv_next(edition):
    """
    Définition unique du « next » TV : premier match SCHEDULED (plus petit
    order_index) de la première PlayDay de date >= aujourd'hui qui a encore
    des SCHEDULED ordonnés ; à défaut, pas de repli (ni journée passée, ni
    hors séquence) — retourne None.
    Ne pack pas le match (voir _pack_match) : à la charge de l'appelant.
    """
    play_days = (
        PlayDay.objects.filter(edition=edition, date__gte=timezone.localdate())
        .order_by("date")
    )

    for play_day in play_days:
        match = (
            Match.objects.filter(
                edition=edition,
                status=Match.Status.SCHEDULED,
                scheduled_time__date=play_day.date,
                order_index__isnull=False,
            )
            .select_related(
                "event",
                "event__category",
                "court",
                "side_a",
                "side_a__player",
                "side_b",
                "side_b__player",
                "group",
            )
            .order_by("order_index")
            .first()
        )
        if match is not None:
            return match

    return None


@require_GET
def api_tv_upcoming(request):
    """
    GET /api/tv/upcoming/
    Lecture publique. Retourne le next match et les N prochains matchs planifiés
    de la journée courante (ou prochaine), pour la TV (slide Programme + bandeau).
    Paramètre ?n=5 (défaut 5, max 10).
    """
    edition = get_current_edition()
    if edition is None:
        return JsonResponse({"next": None, "upcoming": [], "currentPlayDay": None})

    try:
        n = min(int(request.GET.get("n", 5)), 10)
    except (ValueError, TypeError):
        n = 5

    current_pd = (
        PlayDay.objects.filter(edition=edition, date__gte=timezone.localdate())
        .order_by("date")
        .first()
    )
    if current_pd is None:
        return JsonResponse({"next": None, "upcoming": [], "currentPlayDay": None})

    matches = (
        Match.objects.filter(
            edition=edition,
            status=Match.Status.SCHEDULED,
            scheduled_time__date=current_pd.date,
            order_index__isnull=False,
        )
        .select_related(
            "court",
            "side_a",
            "side_a__player",
            "side_b",
            "side_b__player",
            "group",
            "event",
        )
        .order_by("order_index")[:n]
    )

    matches_list = list(matches)
    next_match = matches_list[0] if matches_list else None

    return JsonResponse({
        "next": _pack_match(next_match) if next_match else None,
        "upcoming": [_pack_match(m) for m in matches_list],
        "currentPlayDay": _pack_play_day(current_pd),
    })


# ── Sprint 12 — Ajustements en cours de jeu ──────────────────────────────────

@require_POST
@superuser_required
@transaction.atomic
def api_entry_withdraw(request, entry_id):
    """POST /api/entries/<id>/withdraw/ — forfait / retrait d'un inscrit (EN_COURS requis).
    Body JSON optionnel : {remove_from_group: bool}. Si True, l'entry est en
    plus retirée de l'affichage poule (« retrait sans remplaçant » de la spec).
    Réponse : {entry, matchesWalkover}."""
    data, err = _json_body(request)
    if err:
        return err
    entry = get_object_or_404(Entry.objects.select_related("event", "player", "team"), pk=entry_id)
    try:
        result = withdraw_entry(entry, remove_from_group=bool(data.get("remove_from_group", False)))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=409)
    return JsonResponse({"entry": _pack_entry(entry), "matchesWalkover": result["matches_walkover"]})


@require_POST
@superuser_required
@transaction.atomic
def api_entry_add_late(request, event_id):
    """POST /api/events/<id>/entries/late/ — ajout tardif d'un inscrit dans une poule.
    Body JSON : {group_id, player?, team?}.
    Réponse : {entry, createdCount, overCapacity}."""
    data, err = _json_body(request)
    if err:
        return err

    event = get_object_or_404(Event, pk=event_id)
    group_id = data.get("group_id")
    if not group_id:
        return JsonResponse({"error": "group_id est requis"}, status=400)
    group = get_object_or_404(Group, pk=group_id, event=event)

    player = None
    team = None
    if "player" in data and data["player"] is not None:
        player = get_object_or_404(Player, pk=data["player"])
    if "team" in data and data["team"] is not None:
        team = get_object_or_404(Team, pk=data["team"])

    try:
        entry, created_count, over_capacity = add_late_entry(event, group, player=player, team=team)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "entry": _pack_entry(entry),
        "createdCount": created_count,
        "overCapacity": over_capacity,
    })


@require_POST
@superuser_required
@transaction.atomic
def api_entry_replace(request, entry_id):
    """POST /api/entries/<id>/replace/ — remplace le joueur/équipe d'un inscrit.
    Body JSON : {player?, team?}.
    Réponse : {entry}."""
    data, err = _json_body(request)
    if err:
        return err

    entry = get_object_or_404(Entry.objects.select_related("event__category", "player", "team"), pk=entry_id)

    player = None
    team = None
    if "player" in data and data["player"] is not None:
        player = get_object_or_404(Player, pk=data["player"])
    if "team" in data and data["team"] is not None:
        team = get_object_or_404(Team, pk=data["team"])

    try:
        entry = replace_entry_player(entry, player=player, team=team)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"entry": _pack_entry(entry)})

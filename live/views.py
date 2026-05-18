from collections import defaultdict
from django.shortcuts import render
from django.db.models import Case, When, Value, IntegerField
from competition.models import Event, GroupStanding, GroupMembership
from live.models import Match
from core.models import get_current_edition
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect


def score_state(request):
    edition = get_current_edition()
    if not edition:
        return JsonResponse({"edition": None})

    hero = get_hero_match(edition)
    nxt = get_next_match(edition)

    def stage_label(m):
        if m.stage == Match.Stage.GROUP:
            if m.group and m.group.name:
                return f"Match de poule — Poule {m.group.name}"
            return "Match de poule"
        if m.stage == Match.Stage.QF:
            return "Quart de finale"
        if m.stage == Match.Stage.SF:
            return "Demi-finale"
        if m.stage == Match.Stage.F:
            return "Finale"
        return ""

    def stage_event_label(m):
        base = stage_label(m)
        category_name = m.event.category.name if m.event and m.event.category else ""
        if base and category_name:
            return f"{base} — {category_name}"
        return base or category_name

    def pack(m):
        if not m:
            return None

        # points tennis affichables
        if m.tb_active:
            points_a, points_b = str(m.tb_points_a), str(m.tb_points_b)
        else:
            pa, pb = m.tennis_point_display()
            points_a, points_b = pa, pb

        # clock
        clock = "00:00"
        if m.started_at:
            delta = timezone.now() - m.started_at
            s = int(delta.total_seconds())
            clock = f"{s//60:02d}:{s%60:02d}"

        scheduled_str = (
            timezone.localtime(m.scheduled_time).strftime("%Hh%M")
            if m.scheduled_time else None
        )

        return {
            "id": m.id,
            "status": m.status,
            "server": m.server,
            "court": m.court.name if m.court else None,
            "event": str(m.event),
            "side_a": str(m.side_a),
            "side_b": str(m.side_b),
            "sets_a": m.sets_a,
            "sets_b": m.sets_b,
            "games_a": m.games_a,
            "games_b": m.games_b,
            "tb_active": m.tb_active,
            "points_a": points_a,
            "points_b": points_b,
            "clock": clock,
            "scheduled_str": scheduled_str,
            "order_index": m.order_index,
            "stage_label": stage_label(m),
            "stage_event_label": stage_event_label(m),
        }

    return JsonResponse({
        "edition_year": edition.year,
        "hero": pack(hero),
        "next": pack(nxt),
        "now": timezone.localtime(timezone.now()).strftime("%Hh%M"),
    })


def home(request):
    return render(request, "live/home.html")


def get_hero_match(edition):
    return (
        Match.objects.filter(edition=edition, status=Match.Status.LIVE)
        .select_related("event", "event__category", "court", "side_a", "side_b")
        .order_by("-is_featured", "-updated_at")
        .first()
    )


def get_next_match(edition):
    return (
        Match.objects.filter(edition=edition, status=Match.Status.SCHEDULED)
        .select_related("event", "event__category", "court", "side_a", "side_b")
        .annotate(
            _order_is_null=Case(
                When(order_index__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            _sched_is_null=Case(
                When(scheduled_time__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by(
            "_order_is_null",
            "order_index",
            "_sched_is_null",
            "scheduled_time",
            "id",
        )
        .first()
    )


def build_event_group_tables(edition, events):
    """
    Construit, pour chaque event, la liste de tables par poule :
    - entries (ordre standings si dispo, sinon ordre d'inscription)
    - cell[(row_id, col_id)] = jeux marqués par row (uniquement pour matchs FINISHED)
    - standing_by_entry_id
    - qualif (A1/A2/...)
    """
    event_group_tables = defaultdict(list)

    for ev in events:
        for g in ev.groups.all():
            standings = list(
                GroupStanding.objects.filter(group=g)
                .select_related("entry")
                .order_by("rank", "-points", "-games_won")
            )

            if standings:
                entries = [s.entry for s in standings]
                standing_by_entry_id = {s.entry_id: s for s in standings}
            else:
                memberships = GroupMembership.objects.filter(group=g).select_related("entry")
                entries = [m.entry for m in memberships]
                standing_by_entry_id = {}

            entry_ids = [e.id for e in entries]

            # Tous les matchs de cette poule (terminés ou non), colonnes = matchs
            match_cols = list(
                Match.objects.filter(group=g, stage=Match.Stage.GROUP)
                .select_related("side_a", "side_b")
                .order_by("id")
            )

            # Index : (entry_id, match_id) -> jeux marqués
            cell = {}  # dict[(entry_id, match_id)] = int

            for m in match_cols:
                a_id = m.side_a_id
                b_id = m.side_b_id

                # uniquement si on a les deux participants dans la poule
                if a_id not in entry_ids or b_id not in entry_ids:
                    continue

                # FINISHED ou LIVE : on affiche les jeux (SCHEDULED => vide)
                if m.status in (Match.Status.FINISHED, Match.Status.LIVE):
                    cell[(a_id, m.id)] = m.games_a
                    cell[(b_id, m.id)] = m.games_b

            qualif = {}
            if standings:
                for s in standings:
                    if s.rank and s.rank <= ev.qualified_per_group:
                        qualif[s.entry_id] = f"{g.name}{s.rank}"
                    else:
                        qualif[s.entry_id] = "-"
            else:
                for e in entries:
                    qualif[e.id] = "-"

            event_group_tables[ev.id].append({
                "group": g,
                "entries": entries,
                "match_cols": match_cols,   # <-- AJOUT
                "cell": cell,
                "standing_by_entry_id": standing_by_entry_id,
                "qualif": qualif,
            })

    return dict(event_group_tables)


def results(request):
    edition = get_current_edition()
    if not edition:
        return render(request, "live/results.html", {"edition": None})

    hero_match = get_hero_match(edition)

    match_clock_left = ""
    match_clock_right = ""

    if hero_match:
        # heure (ex: 15h45)
        match_clock_left = timezone.localtime(timezone.now()).strftime("%Hh%M")

        # temps écoulé (ex: 13:00)
        if hero_match.started_at:
            delta = timezone.now() - hero_match.started_at
            total_seconds = int(delta.total_seconds())
            mm = total_seconds // 60
            ss = total_seconds % 60
            match_clock_right = f"{mm:02d}:{ss:02d}"
        else:
            match_clock_right = "00:00"

    next_match = get_next_match(edition)

    events = (
        Event.objects.filter(edition=edition)
        .select_related("category", "edition")
        .prefetch_related("groups")
        .order_by("category__name")
    )

    event_group_tables = build_event_group_tables(edition, events)

    context = {
        "edition": edition,
        "hero_match": hero_match,
        "next_match": next_match,
        "events": events,
        "event_group_tables": event_group_tables,
        "match_clock_left": match_clock_left,
        "match_clock_right": match_clock_right,
    }

    return render(request, "live/results.html", context)


def results_live_menu(request):
    edition = get_current_edition()
    return render(request, "live/results_live_menu.html", {"edition": edition})


def results_poules(request):
    edition = get_current_edition()
    if not edition:
        return render(request, "live/results_poules.html", {"edition": None})

    events = (
        Event.objects.filter(edition=edition)
        .select_related("category", "edition")
        .prefetch_related("groups")
        .order_by("category__name")
    )

    event_group_tables = build_event_group_tables(edition, events)

    return render(request, "live/results_poules.html", {
        "edition": edition,
        "events": events,
        "event_group_tables": event_group_tables,
    })


def results_poules_start(request):
    edition = get_current_edition()
    if not edition:
        # pas d'édition → on peut renvoyer vers la home ou une page info
        return redirect("home")

    first_event = (
        Event.objects
        .filter(edition=edition)
        .select_related("category")
        .order_by("id")
        .first()
    )

    if not first_event:
        return redirect("home")

    return redirect("results_poules_event", event_id=first_event.id)


def results_poules_event(request, event_id: int):
    edition = get_current_edition()
    if not edition:
        return render(request, "live/results_poules_event.html", {"edition": None})

    event = get_object_or_404(
        Event.objects.select_related("category", "edition").prefetch_related("groups"),
        id=event_id,
        edition=edition,
    )

    # rotation: liste des events de l'édition
    events = list(
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("id")
    )
    idx = next((i for i, e in enumerate(events) if e.id == event.id), 0)
    next_event = events[(idx + 1) % len(events)] if events else None

    event_group_tables = build_event_group_tables(edition, [event])

    return render(request, "live/results_poules_event.html", {
        "edition": edition,
        "event": event,
        "event_group_tables": event_group_tables,
        "next_event": next_event,
    })


def results_final_start(request):
    edition = get_current_edition()
    if not edition:
        return redirect("home")

    first_event = (
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("id")
        .first()
    )
    if not first_event:
        return redirect("home")

    return redirect("results_final_event", event_id=first_event.id)


def results_final_event(request, event_id: int):
    edition = get_current_edition()
    if not edition:
        return render(request, "live/results_final_event.html", {"edition": None})

    event = get_object_or_404(
        Event.objects.select_related("category", "edition"),
        id=event_id,
        edition=edition,
    )

    # Auto-réparation: propage les vainqueurs déjà connus vers le tour suivant.
    from live.bracket import sync_final_winners_for_event
    sync_final_winners_for_event(event)

    events = list(
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("id")
    )
    idx = next((i for i, e in enumerate(events) if e.id == event.id), 0)
    next_event = events[(idx + 1) % len(events)] if events else None

    # On récupère les matchs du tableau final
    finals = (
        Match.objects.filter(event=event, stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F])
        .select_related("side_a", "side_b")
        .order_by("stage", "bracket_slot")
    )

    has_bracket = finals.exists()
    qf = list(finals.filter(stage=Match.Stage.QF).order_by("bracket_slot"))
    sf = list(finals.filter(stage=Match.Stage.SF).order_by("bracket_slot"))
    f1 = finals.filter(stage=Match.Stage.F, bracket_slot="F1").first()
    show_qf = len(qf) > 0

    def _winner_score_text(m):
        if not m or m.status != Match.Status.FINISHED:
            return ""
        if int(m.best_of or 1) == 1:
            if m.winner_side == "A":
                return f"{m.games_a}/{m.games_b}"
            if m.winner_side == "B":
                return f"{m.games_b}/{m.games_a}"
            return f"{m.games_a}/{m.games_b}"
        if m.winner_side == "A":
            return f"{m.sets_a}-{m.sets_b}"
        if m.winner_side == "B":
            return f"{m.sets_b}-{m.sets_a}"
        return f"{m.sets_a}-{m.sets_b}"

    def _winner_sets_detail_text(m):
        if not m or m.status != Match.Status.FINISHED or m.winner_side not in ("A", "B"):
            return ""
        winner_is_a = m.winner_side == "A"
        parts = []
        for s in (m.set_scores or []):
            mode = (s or {}).get("mode")
            if mode == "SUPER_TB":
                a = (s or {}).get("tb_a")
                b = (s or {}).get("tb_b")
            else:
                a = (s or {}).get("a")
                b = (s or {}).get("b")
            if a is None or b is None:
                continue
            left = a if winner_is_a else b
            right = b if winner_is_a else a
            parts.append(f"{left}/{right}")
        if parts:
            return " ".join(parts)
        return _winner_score_text(m)

    by_slot = {m.bracket_slot: m for m in finals if m.bracket_slot}
    carry_scores_a = {}
    carry_scores_b = {}

    # Pour afficher en demi/finale le score du tour précédent si le match n'est pas encore joué.
    for sfm in sf:
        if not sfm:
            continue
        src_a = by_slot.get("QF1") if sfm.bracket_slot == "SF1" else by_slot.get("QF3")
        src_b = by_slot.get("QF2") if sfm.bracket_slot == "SF1" else by_slot.get("QF4")
        if src_a and src_a.status == Match.Status.FINISHED:
            carry_scores_a[sfm.id] = _winner_score_text(src_a)
        if src_b and src_b.status == Match.Status.FINISHED:
            carry_scores_b[sfm.id] = _winner_score_text(src_b)

    if f1:
        src_a = by_slot.get("SF1")
        src_b = by_slot.get("SF2")
        if src_a and src_a.status == Match.Status.FINISHED:
            carry_scores_a[f1.id] = _winner_score_text(src_a)
        if src_b and src_b.status == Match.Status.FINISHED:
            carry_scores_b[f1.id] = _winner_score_text(src_b)

    if has_bracket:
        # Padding pour éviter les index errors dans le template
        if show_qf:
            while len(qf) < 4:
                qf.append(None)
        while len(sf) < 2:
            sf.append(None)

    final_winner_scores = _winner_sets_detail_text(f1) if f1 else ""

    return render(request, "live/results_final_event.html", {
        "edition": edition,
        "event": event,
        "next_event": next_event,
        "qf": qf,
        "sf": sf,
        "final": f1,
        "has_bracket": has_bracket,
        "show_qf": show_qf,
        "carry_scores_a": carry_scores_a,
        "carry_scores_b": carry_scores_b,
        "final_winner_scores": final_winner_scores,
    })


def results_mix_start(request):
    edition = get_current_edition()
    if not edition:
        return redirect("home")

    first_event = (
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("id")
        .first()
    )
    if not first_event:
        return redirect("home")

    return redirect("results_mix_event", event_id=first_event.id)


def results_mix_event(request, event_id: int):
    edition = get_current_edition()
    if not edition:
        return render(request, "live/results_mix_event.html", {"edition": None})

    event = get_object_or_404(
        Event.objects.select_related("category", "edition").prefetch_related("groups"),
        id=event_id,
        edition=edition,
    )

    events = list(
        Event.objects.filter(edition=edition)
        .select_related("category")
        .order_by("id")
    )
    idx = next((i for i, e in enumerate(events) if e.id == event.id), 0)
    next_event = events[(idx + 1) % len(events)] if events else None

    event_group_tables = build_event_group_tables(edition, [event]).get(event.id, [])

    from live.bracket import sync_final_winners_for_event
    sync_final_winners_for_event(event)

    finals = (
        Match.objects.filter(event=event, stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F])
        .select_related("side_a", "side_b")
        .order_by("stage", "bracket_slot")
    )
    qf = list(finals.filter(stage=Match.Stage.QF).order_by("bracket_slot"))
    sf = list(finals.filter(stage=Match.Stage.SF).order_by("bracket_slot"))
    f1 = finals.filter(stage=Match.Stage.F, bracket_slot="F1").first()
    show_qf = len(qf) > 0
    has_bracket = finals.exists()

    if has_bracket:
        if show_qf:
            while len(qf) < 4:
                qf.append(None)
        while len(sf) < 2:
            sf.append(None)

    final_winner_scores = ""
    if f1 and f1.status == Match.Status.FINISHED:
        winner_is_a = f1.winner_side == "A"
        parts = []
        for s in (f1.set_scores or []):
            mode = (s or {}).get("mode")
            if mode == "SUPER_TB":
                a = (s or {}).get("tb_a")
                b = (s or {}).get("tb_b")
            else:
                a = (s or {}).get("a")
                b = (s or {}).get("b")
            if a is None or b is None:
                continue
            parts.append(f"{a}/{b}" if winner_is_a else f"{b}/{a}")
        if parts:
            final_winner_scores = " ".join(parts)
        elif int(f1.best_of or 1) == 1:
            final_winner_scores = (
                f"{f1.games_a}/{f1.games_b}" if winner_is_a else f"{f1.games_b}/{f1.games_a}"
            )
        else:
            final_winner_scores = (
                f"{f1.sets_a}-{f1.sets_b}" if winner_is_a else f"{f1.sets_b}-{f1.sets_a}"
            )

    return render(request, "live/results_mix_event.html", {
        "edition": edition,
        "event": event,
        "next_event": next_event,
        "group_tables": event_group_tables,
        "qf": qf,
        "sf": sf,
        "final": f1,
        "show_qf": show_qf,
        "has_bracket": has_bracket,
        "final_winner_scores": final_winner_scores,
    })

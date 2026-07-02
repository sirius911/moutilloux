import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from core.models import TournamentEdition
from competition.models import Event
from .models import Match
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from competition.standings import recalc_one_group
from live.admin_views import start_match


def is_referee(user):
    return user.is_authenticated and (user.groups.filter(name="Arbitre").exists() or user.is_superuser)


referee_required = user_passes_test(
    is_referee,
    login_url="/accounts/login/",
    )


class RefSelectForm(forms.Form):
    edition = forms.ModelChoiceField(queryset=TournamentEdition.objects.order_by("-year"),
                                     required=False, label="Édition")
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=True, label="Épreuve")
    match = forms.ModelChoiceField(queryset=Match.objects.none(), required=True, label="Match")

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop("edition", None)
        event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)

        if edition:
            self.fields["event"].queryset = Event.objects.filter(edition=edition).order_by("category__name")
        if event:
            # on propose : match en cours + matchs ordonnés + matchs non finis
            qs = Match.objects.filter(event=event).exclude(status=Match.Status.FINISHED)
            qs = qs.order_by("-is_featured", "order_index", "id")
            self.fields["match"].queryset = qs


@login_required
@referee_required
def referee_home(request):
    edition_default = TournamentEdition.objects.filter(is_active=True).order_by("-year").first()

    # valeurs courantes (GET prioritaire, sinon POST)
    edition_id = request.GET.get("edition") or request.POST.get("edition")
    event_id = request.GET.get("event") or request.POST.get("event")

    edition = TournamentEdition.objects.filter(id=edition_id).first() if edition_id else edition_default
    event = Event.objects.filter(id=event_id).first() if event_id else None

    form = RefSelectForm(
        request.POST if request.method == "POST" else None,
        edition=edition,
        event=event,
        initial={"edition": edition, "event": event}
    )

    if request.method == "POST" and form.is_valid():
        m = form.cleaned_data["match"]
        return redirect("referee_match", match_id=m.id)

    return render(request, "live/referee_home.html", {
        "form": form,
        "edition": edition,
        "event": event,
    })


@login_required
@referee_required
def referee_match(request, match_id: int):
    match = get_object_or_404(Match.objects.select_related("event", "side_a", "side_b"), id=match_id)

    swap = bool(request.session.get(f"swap_match_{match.id}", False))

    left = match.side_b if swap else match.side_a
    right = match.side_a if swap else match.side_b

    # service côté affichage
    # server stocké en BDD = "A" ou "B"
    serving_side = match.side_a if match.server == "A" else match.side_b
    serving_display = (match.side_b if serving_side == match.side_a else match.side_a) if swap else serving_side

    return render(request, "live/referee_match.html", {
        "match": match,
        "left": left,
        "right": right,
        "swap": swap,
        "serving_display": serving_display,
    })


@login_required
@referee_required
@require_POST
@transaction.atomic
def referee_action(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)

    # Accepte aussi bien un corps JSON (SPA Vue via useApi) qu'un POST form
    # (template arbitre existant). Les deux supports .get()/in/[] de la même façon.
    if request.content_type and request.content_type.startswith("application/json"):
        try:
            data = json.loads(request.body or b"{}")
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "error": "Corps JSON invalide"}, status=400)
    else:
        data = request.POST

    action = data.get("action")

    # Garde-fou pour les anciens matchs créés avant les presets complets.
    if match.match_format == Match.Format.BO3 and int(match.best_of or 1) != 3:
        match.best_of = 3
        match.games_to_win = 6
        match.tb_at = 6
        match.tb_points_to_win = 7
        if not match.deciding_set_mode:
            match.deciding_set_mode = Match.DecidingSetMode.FULL_SET
        if not match.deciding_tb_points_to_win:
            match.deciding_tb_points_to_win = 10
        match.save(update_fields=[
            "best_of", "games_to_win", "tb_at", "tb_points_to_win",
            "deciding_set_mode", "deciding_tb_points_to_win",
        ])

    swap_key = f"swap_match_{match_id}"
    swap = bool(request.session.get(swap_key, False))

    # Sécurité : si match terminé, refuser certaines actions sauf "reopen" et "edit"
    if match.status == Match.Status.FINISHED and action not in ("reopen", "edit"):
        return JsonResponse({"ok": False, "error": "Match terminé. Réouvre-le si besoin."}, status=400)

    def rules():
        # Si tu veux que MANUAL désactive toute logique auto
        if match.match_format == Match.Format.MANUAL:
            return 999, 999, 1, 999, True

        return (
            int(match.games_to_win),
            int(match.tb_at),
            int(match.best_of),
            int(match.tb_points_to_win),
            bool(match.tb_win_by_two),
        )

    def is_deciding_set_super_tb():
        games_to_win, tb_at, best_of, tb_to_win, tb_by2 = rules()
        return (
            match.deciding_set_mode == Match.DecidingSetMode.SUPER_TB
            and best_of > 1
            and match.sets_a == match.sets_b
            and (match.sets_a + match.sets_b) == (best_of - 1)
        )

    def append_set_score(a_games=None, b_games=None, tb_a=None, tb_b=None, mode="SET"):
        if not isinstance(match.set_scores, list):
            match.set_scores = []
        item = {
            "set_no": len(match.set_scores) + 1,
            "mode": mode,
            "a": a_games,
            "b": b_games,
        }
        if tb_a is not None and tb_b is not None:
            item["tb_a"] = int(tb_a)
            item["tb_b"] = int(tb_b)
        match.set_scores.append(item)

    # ---------- Helpers mapping gauche/droite -> A/B selon swap ----------
    def side_from_left() -> str:
        return "B" if swap else "A"

    def side_from_right() -> str:
        return "A" if swap else "B"

    # ---------- Helpers score ----------

    def clamp_non_negative(x: int) -> int:
        return x if x > 0 else 0

    def reset_points():
        match.points_a = 0
        match.points_b = 0

    def reset_tiebreak():
        match.tb_active = False
        match.tb_points_a = 0
        match.tb_points_b = 0

    def switch_server():
        match.server = "B" if match.server == "A" else "A"

    def after_game_awarded():
        """
        Appelé après avoir donné un jeu (quel que soit le moyen: points ou bouton 'Jeu').
        - reset points
        - switch serveur
        - déclenche TB si on arrive à tb_at - tb_at
        - sinon check set/match (hors TB)
        """
        games_to_win, tb_at, best_of, tb_to_win, tb_by2 = rules()

        # Nouveau jeu: points à 0
        match.points_a = 0
        match.points_b = 0

        # Inversion serveur à chaque jeu
        match.server = "B" if match.server == "A" else "A"

        # Déclenchement TB (4-4 ou 5-5 selon format)
        if match.games_a == tb_at and match.games_b == tb_at:
            match.tb_active = True
            match.tb_points_a = 0
            match.tb_points_b = 0
            return  # on ne calcule pas set/match maintenant

        # Sinon, on teste set/match normal
        maybe_finish_set_and_match()

    def maybe_finish_set_and_match(set_winner_side: str | None = None, tb_points=None, super_tb=False):
        """
        Si set_winner_side est fourni (A/B), on force la victoire du set (cas tie-break gagné).
        Sinon, on teste la condition de set hors tie-break.
        """
        games_to_win, tb_at, best_of, tb_to_win, tb_by2 = rules()

        ga, gb = match.games_a, match.games_b

        # --- Cas tie-break gagné ---
        if set_winner_side in ("A", "B"):
            if super_tb:
                append_set_score(
                    a_games=None,
                    b_games=None,
                    tb_a=tb_points[0] if tb_points else None,
                    tb_b=tb_points[1] if tb_points else None,
                    mode="SUPER_TB",
                )
            else:
                append_set_score(
                    a_games=match.games_a,
                    b_games=match.games_b,
                    tb_a=tb_points[0] if tb_points else None,
                    tb_b=tb_points[1] if tb_points else None,
                    mode="TB_SET",
                )

            if set_winner_side == "A":
                match.sets_a += 1
            else:
                match.sets_b += 1

            sets_needed = (best_of // 2) + 1

            # Match terminé ?
            if match.sets_a >= sets_needed or match.sets_b >= sets_needed:
                match.status = Match.Status.FINISHED
                match.is_featured = False
                match.winner_side = "A" if match.sets_a > match.sets_b else "B"

                # on garde games_a/games_b comme score final du set si match en 1 set
                match.points_a = 0
                match.points_b = 0
                reset_tiebreak()
                # ✅ Recalcul classement poule
                if match.stage == Match.Stage.GROUP and match.group_id:
                    gid = match.group_id
                    _ev = match.event
                    transaction.on_commit(lambda: recalc_one_group(gid))
                    from live.bracket import sync_final_bracket_for_event
                    transaction.on_commit(lambda ev=_ev: sync_final_bracket_for_event(ev))
                if match.stage in (Match.Stage.QF, Match.Stage.SF):
                    from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
                    transaction.on_commit(lambda: sync_final_winners_for_event(match.event))
                    transaction.on_commit(lambda: sync_p3_losers_for_event(match.event))
                return

            # Sinon BO3 : set suivant
            match.games_a = 0
            match.games_b = 0
            match.points_a = 0
            match.points_b = 0
            if is_deciding_set_super_tb():
                match.tb_active = True
                match.tb_points_a = 0
                match.tb_points_b = 0
            else:
                reset_tiebreak()
            return

        # --- Cas hors tie-break : set gagné si games_to_win atteint + 2 jeux d'écart ---
        if (ga >= games_to_win or gb >= games_to_win) and abs(ga - gb) >= 2:
            append_set_score(a_games=ga, b_games=gb, mode="SET")

            if ga > gb:
                match.sets_a += 1
            else:
                match.sets_b += 1

            sets_needed = (best_of // 2) + 1

            if match.sets_a >= sets_needed or match.sets_b >= sets_needed:
                match.status = Match.Status.FINISHED
                match.is_featured = False
                match.winner_side = "A" if match.sets_a > match.sets_b else "B"

                # IMPORTANT: on garde games_a/games_b comme score final du set en 1 set
                match.points_a = 0
                match.points_b = 0
                reset_tiebreak()
                # ✅ Recalcul classement poule
                if match.stage == Match.Stage.GROUP and match.group_id:
                    gid = match.group_id
                    _ev = match.event
                    transaction.on_commit(lambda: recalc_one_group(gid))
                    from live.bracket import sync_final_bracket_for_event
                    transaction.on_commit(lambda ev=_ev: sync_final_bracket_for_event(ev))
                if match.stage in (Match.Stage.QF, Match.Stage.SF):
                    from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
                    transaction.on_commit(lambda: sync_final_winners_for_event(match.event))
                    transaction.on_commit(lambda: sync_p3_losers_for_event(match.event))
                return

            # BO3 : set suivant
            match.games_a = 0
            match.games_b = 0
            match.points_a = 0
            match.points_b = 0
            if is_deciding_set_super_tb():
                match.tb_active = True
                match.tb_points_a = 0
                match.tb_points_b = 0
            else:
                reset_tiebreak()
            return

    def award_point_to(side: str):
        """
        Ajoute un point à A/B.
        - Si tie-break actif: incrémente tb_points_* et gère victoire TB.
        - Sinon: incrémente points_* et gère victoire de jeu (>=4 et 2 d'écart).
        """
        games_to_win, tb_at, best_of, tb_to_win, tb_by2 = rules()

        # -------------------------
        # TIE-BREAK MODE
        # -------------------------
        if match.tb_active:
            if side == "A":
                match.tb_points_a += 1
            else:
                match.tb_points_b += 1

            # Service auto en TB : somme impaire => switch serveur
            total = match.tb_points_a + match.tb_points_b
            if total % 2 == 1:
                match.server = "B" if match.server == "A" else "A"

            ta, tb = match.tb_points_a, match.tb_points_b
            target_tb = int(match.deciding_tb_points_to_win) if is_deciding_set_super_tb() else tb_to_win

            # Condition de victoire TB : tb_to_win, + 2 points si tb_by2
            if tb_by2:
                tb_won = (ta >= target_tb or tb >= target_tb) and abs(ta - tb) >= 2
            else:
                tb_won = (ta >= target_tb or tb >= target_tb)

            if tb_won:
                tb_winner = "A" if ta > tb else "B"

                super_tb = is_deciding_set_super_tb()
                # TB de set normal -> 7/6 ; super TB décisif -> pas de jeux
                if not super_tb:
                    if tb_winner == "A":
                        match.games_a += 1
                    else:
                        match.games_b += 1

                maybe_finish_set_and_match(
                    set_winner_side=tb_winner,
                    tb_points=(ta, tb),
                    super_tb=super_tb,
                )

                match.points_a = 0
                match.points_b = 0
                reset_tiebreak()
                return

            return  # TB continue

        # -------------------------
        # NORMAL GAME MODE
        # -------------------------
        if side == "A":
            match.points_a += 1
        else:
            match.points_b += 1

        pa, pb = match.points_a, match.points_b

        # Jeu gagné si >=4 et 2 points d'écart
        if (pa >= 4 or pb >= 4) and abs(pa - pb) >= 2:
            if pa > pb:
                match.games_a += 1
            else:
                match.games_b += 1

            match.points_a = 0
            match.points_b = 0

            # switch serveur à chaque jeu
            match.server = "B" if match.server == "A" else "A"

            # Déclenche TB au score tb_at - tb_at
            if match.games_a == tb_at and match.games_b == tb_at:
                match.tb_active = True
                match.tb_points_a = 0
                match.tb_points_b = 0
                return

            maybe_finish_set_and_match()

    # ---------- Actions ----------
    if action == "swap":
        request.session[swap_key] = not swap
        return JsonResponse({"ok": True})

    if action == "point_left":
        award_point_to(side_from_left())
        match.save(update_fields=[
            "points_a", "points_b",
            "games_a", "games_b",
            "sets_a", "sets_b",
            "set_scores",
            "server",
            "tb_active", "tb_points_a", "tb_points_b",
            "status", "is_featured",
            "winner_side",
        ])
        return JsonResponse({"ok": True})

    if action == "point_right":
        award_point_to(side_from_right())
        match.save(update_fields=[
            "points_a", "points_b",
            "games_a", "games_b",
            "sets_a", "sets_b",
            "set_scores",
            "server",
            "tb_active", "tb_points_a", "tb_points_b",
            "status", "is_featured",
            "winner_side",
        ])
        return JsonResponse({"ok": True})

    if action == "server_left":
        match.server = side_from_left()
        match.save(update_fields=["server"])
        return JsonResponse({"ok": True})

    if action == "server_right":
        match.server = side_from_right()
        match.save(update_fields=["server"])
        return JsonResponse({"ok": True})

    if action == "toggle_service":
        # En TB: autorisé uniquement à 0-0 TB
        if match.tb_active:
            if (match.tb_points_a + match.tb_points_b) != 0:
                return JsonResponse({"ok": False,
                                     "error": "Service modifiable seulement au début du tie-break (0-0)"},
                                    status=400)
            match.server = "B" if match.server == "A" else "A"
            match.save(update_fields=["server"])
            return JsonResponse({"ok": True})

        # Hors TB: autorisé uniquement à 0-0 du jeu
        if match.points_a != 0 or match.points_b != 0:
            return JsonResponse({"ok": False, "error": "Impossible de changer le service en cours de jeu"}, status=400)

        match.server = "B" if match.server == "A" else "A"
        match.save(update_fields=["server"])
        return JsonResponse({"ok": True})

    if action == "reset_points":
        reset_points()
        match.save(update_fields=["points_a", "points_b"])
        return JsonResponse({"ok": True})

    # --- Jeux / Sets manuel (on garde ton comportement actuel) ---
    if action == "game_left":
        # Interdit de modifier les jeux via ce bouton si TB en cours (sinon incohérent)
        if match.tb_active:
            return JsonResponse({"ok": False,
                                 "error": "Impossible d'ajouter un jeu pendant un tie-break."
                                " Termine le tie-break ou réinitialise."}, status=400)

        if side_from_left() == "A":
            match.games_a += 1
        else:
            match.games_b += 1

        after_game_awarded()

        match.save(update_fields=[
            "games_a", "games_b",
            "points_a", "points_b",
            "server",
            "tb_active", "tb_points_a", "tb_points_b",
            "sets_a", "sets_b",
            "set_scores",
            "status", "is_featured",
            "winner_side",
        ])
        return JsonResponse({"ok": True})

    if action == "game_right":
        if match.tb_active:
            return JsonResponse({"ok": False,
                                 "error": "Impossible d'ajouter un jeu pendant un tie-break."
                                " Termine le tie-break ou réinitialise."}, status=400)

        if side_from_right() == "A":
            match.games_a += 1
        else:
            match.games_b += 1

        after_game_awarded()

        match.save(update_fields=[
            "games_a", "games_b",
            "points_a", "points_b",
            "server",
            "tb_active", "tb_points_a", "tb_points_b",
            "sets_a", "sets_b",
            "set_scores",
            "status", "is_featured",
            "winner_side",
        ])
        return JsonResponse({"ok": True})

    if action == "set_left":
        if side_from_left() == "A":
            match.sets_a += 1
        else:
            match.sets_b += 1
        match.games_a = 0
        match.games_b = 0
        reset_points()
        reset_tiebreak()
        match.save(update_fields=["sets_a",
                                  "sets_b",
                                  "games_a",
                                  "games_b",
                                  "points_a",
                                  "points_b",
                                  "tb_active",
                                  "tb_points_a",
                                  "tb_points_b"])
        return JsonResponse({"ok": True})

    if action == "set_right":
        if side_from_right() == "A":
            match.sets_a += 1
        else:
            match.sets_b += 1
        match.games_a = 0
        match.games_b = 0
        reset_points()
        reset_tiebreak()
        match.save(update_fields=["sets_a",
                                  "sets_b",
                                  "games_a",
                                  "games_b",
                                  "points_a",
                                  "points_b",
                                  "tb_active",
                                  "tb_points_a",
                                  "tb_points_b"])
        return JsonResponse({"ok": True})

    # --- Démarrer / finir / réouvrir ---
    if action == "start":
        start_match(match)
        return JsonResponse({"ok": True})

    if action == "finish_left":
        match.winner_side = side_from_left()
        match.is_featured = False
        match.mark_finished()   # ✅ met status=FINISHED + finished_at
        match.save()

        if match.stage == Match.Stage.GROUP and match.group_id:
            gid = match.group_id
            _ev_left = match.event
            transaction.on_commit(lambda: recalc_one_group(gid))
            from live.bracket import sync_final_bracket_for_event
            transaction.on_commit(lambda ev=_ev_left: sync_final_bracket_for_event(ev))
        if match.stage in (Match.Stage.QF, Match.Stage.SF):
            from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
            transaction.on_commit(lambda: sync_final_winners_for_event(match.event))
            transaction.on_commit(lambda: sync_p3_losers_for_event(match.event))
        if match.stage == Match.Stage.F:
            _event = match.event
            def _try_close_left(ev=_event):
                from live.admin_views import close_event
                try:
                    close_event(ev)
                except ValueError:
                    pass
            transaction.on_commit(_try_close_left)

        return JsonResponse({"ok": True})

    if action == "finish_right":
        match.winner_side = side_from_right()
        match.is_featured = False
        match.mark_finished()
        match.save()

        if match.stage == Match.Stage.GROUP and match.group_id:
            gid = match.group_id
            _ev_right = match.event
            transaction.on_commit(lambda: recalc_one_group(gid))
            from live.bracket import sync_final_bracket_for_event
            transaction.on_commit(lambda ev=_ev_right: sync_final_bracket_for_event(ev))
        if match.stage in (Match.Stage.QF, Match.Stage.SF):
            from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
            transaction.on_commit(lambda: sync_final_winners_for_event(match.event))
            transaction.on_commit(lambda: sync_p3_losers_for_event(match.event))
        if match.stage == Match.Stage.F:
            _event = match.event
            def _try_close_right(ev=_event):
                from live.admin_views import close_event
                try:
                    close_event(ev)
                except ValueError:
                    pass
            transaction.on_commit(_try_close_right)

        return JsonResponse({"ok": True})

    if action == "finish_winner":
        winner = data.get("winner")
        if winner not in ("A", "B"):
            return JsonResponse({"ok": False, "error": "winner doit être 'A' ou 'B'"}, status=400)

        match.winner_side = winner          # repère modèle direct, pas de swap
        match.is_featured = False
        match.mark_finished()
        match.save()

        if match.stage == Match.Stage.GROUP and match.group_id:
            gid = match.group_id
            _ev_winner = match.event
            transaction.on_commit(lambda: recalc_one_group(gid))
            from live.bracket import sync_final_bracket_for_event
            transaction.on_commit(lambda ev=_ev_winner: sync_final_bracket_for_event(ev))
        if match.stage in (Match.Stage.QF, Match.Stage.SF):
            from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
            transaction.on_commit(lambda: sync_final_winners_for_event(match.event))
            transaction.on_commit(lambda: sync_p3_losers_for_event(match.event))
        if match.stage == Match.Stage.F:
            _event = match.event
            def _try_close_winner(ev=_event):
                from live.admin_views import close_event
                try:
                    close_event(ev)
                except ValueError:
                    pass
            transaction.on_commit(_try_close_winner)

        return JsonResponse({"ok": True})

    if action == "reopen":
        match.status = Match.Status.SCHEDULED
        match.is_featured = False
        match.winner_side = None
        match.set_scores = []
        match.save(update_fields=["status", "is_featured", "winner_side", "set_scores"])

        if match.stage == Match.Stage.GROUP and match.group_id:
            recalc_one_group(match.group_id)

        return JsonResponse({"ok": True})

    if action == "reset_all":
        match.points_a = 0
        match.points_b = 0
        match.games_a = 0
        match.games_b = 0
        match.sets_a = 0
        match.sets_b = 0
        reset_tiebreak()
        match.winner_side = None
        match.set_scores = []
        match.status = Match.Status.SCHEDULED
        match.is_featured = False
        match.save(update_fields=[
            "points_a", "points_b",
            "games_a", "games_b",
            "sets_a", "sets_b",
            "tb_active", "tb_points_a", "tb_points_b",
            "winner_side",
            "set_scores",
            "status", "is_featured",
        ])
        return JsonResponse({"ok": True})

    # Edit manuel complet (simple)
    if action == "edit":
        for field in ["points_a", "points_b", "games_a", "games_b", "sets_a", "sets_b"]:
            if field in data:
                setattr(match, field, int(data[field]))
        if "server" in data:
            match.server = data["server"]  # "A" ou "B"
        match.save()
        return JsonResponse({"ok": True})

    # --- Ajustements manuels : JEUX ---
    if action == "game_left_plus":
        if match.tb_active:
            return JsonResponse({"ok": False, "error": "Impossible de modifier les jeux pendant un tie-break."},
                                status=400)
        if side_from_left() == "A":
            match.games_a += 1
        else:
            match.games_b += 1
        match.save(update_fields=["games_a", "games_b"])
        return JsonResponse({"ok": True})

    if action == "game_left_minus":
        if match.tb_active:
            return JsonResponse({"ok": False, "error": "Impossible de modifier les jeux pendant un tie-break."},
                                status=400)
        if side_from_left() == "A":
            match.games_a = clamp_non_negative(match.games_a - 1)
        else:
            match.games_b = clamp_non_negative(match.games_b - 1)
        match.save(update_fields=["games_a", "games_b"])
        return JsonResponse({"ok": True})

    if action == "game_right_plus":
        if match.tb_active:
            return JsonResponse({"ok": False, "error": "Impossible de modifier les jeux pendant un tie-break."},
                                status=400)
        if side_from_right() == "A":
            match.games_a += 1
        else:
            match.games_b += 1
        match.save(update_fields=["games_a", "games_b"])
        return JsonResponse({"ok": True})

    if action == "game_right_minus":
        if match.tb_active:
            return JsonResponse({"ok": False, "error": "Impossible de modifier les jeux pendant un tie-break."},
                                status=400)
        if side_from_right() == "A":
            match.games_a = clamp_non_negative(match.games_a - 1)
        else:
            match.games_b = clamp_non_negative(match.games_b - 1)
        match.save(update_fields=["games_a", "games_b"])
        return JsonResponse({"ok": True})

    if action == "set_format":
        preset = data.get("format")

        PRESETS = {
            # Ton modèle actuel:
            # GROUP_SET5_TB_4_4 = "G_SET5_TB44"
            # QF_SET5_TB_5_5  = "QF_SET5_TB55"
            # NORMAL_1SET     = "NORMAL_1SET"
            # BO3             = "BO3"
            # MANUAL          = "MANUAL"
            "POULE": dict(match_format=Match.Format.GROUP_SET5_TB_4_4, games_to_win=5, tb_at=4, best_of=1),
            "QUART": dict(match_format=Match.Format.QF_SET5_TB_5_5, games_to_win=6, tb_at=5, best_of=1),
            "DEMI": dict(match_format=Match.Format.NORMAL_1SET, games_to_win=6, tb_at=6, best_of=1),
            "FINALE": dict(
                match_format=Match.Format.BO3, games_to_win=6, tb_at=6, best_of=3,
                deciding_set_mode=Match.DecidingSetMode.FULL_SET, deciding_tb_points_to_win=10,
            ),
            "FINALE_TB": dict(
                match_format=Match.Format.BO3, games_to_win=6, tb_at=6, best_of=3,
                deciding_set_mode=Match.DecidingSetMode.SUPER_TB, deciding_tb_points_to_win=10,
            ),
            "MANUAL": dict(match_format=Match.Format.MANUAL),
        }

        if preset not in PRESETS:
            return JsonResponse({"ok": False, "error": "Preset inconnu"}, status=400)

        preset_data = PRESETS[preset]

        # applique toujours match_format (utile pour libellé/tri)
        match.match_format = preset_data["match_format"]

        # si MANUAL, on coupe toute logique auto
        if match.match_format == Match.Format.MANUAL:
            match.tb_active = False
            match.tb_points_a = 0
            match.tb_points_b = 0
            match.save(update_fields=["match_format", "tb_active", "tb_points_a", "tb_points_b"])
            return JsonResponse({"ok": True})

        # applique les champs modulables
        match.games_to_win = preset_data["games_to_win"]
        match.tb_at = preset_data["tb_at"]
        match.best_of = preset_data["best_of"]

        # tb classique (tu peux changer plus tard si tu veux)
        match.tb_points_to_win = 7
        match.tb_win_by_two = True
        match.deciding_set_mode = preset_data.get("deciding_set_mode", Match.DecidingSetMode.FULL_SET)
        match.deciding_tb_points_to_win = preset_data.get("deciding_tb_points_to_win", 10)

        # Sécurité: si on change de preset, on désactive un TB éventuellement actif
        match.tb_active = False
        match.tb_points_a = 0
        match.tb_points_b = 0

        match.save(update_fields=[
            "match_format",
            "games_to_win", "tb_at", "best_of",
            "tb_points_to_win", "tb_win_by_two",
            "deciding_set_mode", "deciding_tb_points_to_win",
            "tb_active", "tb_points_a", "tb_points_b",
        ])
        return JsonResponse({"ok": True})

    # --- Ajustements manuels : SETS ---
    if action == "set_left_plus":
        if side_from_left() == "A":
            match.sets_a += 1
        else:
            match.sets_b += 1
        match.save(update_fields=["sets_a", "sets_b"])
        return JsonResponse({"ok": True})

    if action == "set_left_minus":
        if side_from_left() == "A":
            match.sets_a = clamp_non_negative(match.sets_a - 1)
        else:
            match.sets_b = clamp_non_negative(match.sets_b - 1)
        match.save(update_fields=["sets_a", "sets_b"])
        return JsonResponse({"ok": True})

    if action == "set_right_plus":
        if side_from_right() == "A":
            match.sets_a += 1
        else:
            match.sets_b += 1
        match.save(update_fields=["sets_a", "sets_b"])
        return JsonResponse({"ok": True})

    if action == "set_right_minus":
        if side_from_right() == "A":
            match.sets_a = clamp_non_negative(match.sets_a - 1)
        else:
            match.sets_b = clamp_non_negative(match.sets_b - 1)
        match.save(update_fields=["sets_a", "sets_b"])
        return JsonResponse({"ok": True})

    if action == "tb_on":
        match.tb_active = True
        match.tb_points_a = 0
        match.tb_points_b = 0
        match.points_a = 0
        match.points_b = 0
        match.save(update_fields=["tb_active", "tb_points_a", "tb_points_b", "points_a", "points_b"])
        return JsonResponse({"ok": True})

    if action == "tb_off":
        match.tb_active = False
        match.tb_points_a = 0
        match.tb_points_b = 0
        match.save(update_fields=["tb_active", "tb_points_a", "tb_points_b"])
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "Action inconnue"}, status=400)

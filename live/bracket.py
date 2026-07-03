from competition.models import Group, GroupStanding
from live.models import Match


def _resolve_label_to_entry(event, label: str):
    if not label or len(label) < 2:
        return None
    group_name = label[0].upper()
    try:
        rank = int(label[1:])
    except ValueError:
        return None

    g = Group.objects.filter(event=event, name__iexact=group_name).first()
    if not g:
        return None

    s = GroupStanding.objects.filter(group=g, rank=rank).select_related("entry").first()
    return s.entry if s else None


def _is_group_label(label: str) -> bool:
    if not label or len(label) < 2:
        return False
    if not label[0].isalpha():
        return False
    return label[1:].isdigit()


def _fmt_for_stage(stage) -> str:
    if stage in (Match.Stage.QF,):
        return Match.Format.QF_SET5_TB_5_5
    if stage == Match.Stage.SF:
        return Match.Format.NORMAL_1SET
    if stage in (Match.Stage.F, Match.Stage.P3):
        return Match.Format.BO3
    return Match.Format.NORMAL_1SET


def _bracket_layout(gnames, qpg):
    """
    Retourne la liste des slots (stage, slot_name, a_label, b_label)
    selon la configuration (N groupes × qpg qualifiés).

    Principes de placement (qpg=2) :
    - Séparation maximale : X1 et X2 d'une même poule sont en demi-tableaux opposés.
    - Les byes vont aux premiers vainqueurs par ordre alphabétique.
    - 1er tour : 1er vs 2e d'une autre poule autant que possible.

    Templates explicites jusqu'à 4 poules (au-delà, non géré).
    """
    N = len(gnames)
    g = gnames

    if qpg == 2:
        if N == 2:
            # Q=4, B=4 — 2 demies + finale
            return [
                (Match.Stage.SF, "SF1", f"{g[0]}1", f"{g[1]}2"),
                (Match.Stage.SF, "SF2", f"{g[1]}1", f"{g[0]}2"),
                (Match.Stage.F,  "F1",  "WSF1",      "WSF2"),
            ]
        if N == 3:
            # Q=6, B=8, 2 byes (A1, B1)
            # QF1 : C1 vs B2 → WQF1 entre dans SF1
            # QF2 : C2 vs A2 → WQF2 entre dans SF2
            # SF1 : A1 (bye) vs WQF1
            # SF2 : B1 (bye) vs WQF2
            return [
                (Match.Stage.QF, "QF1", f"{g[2]}1", f"{g[1]}2"),
                (Match.Stage.QF, "QF2", f"{g[2]}2", f"{g[0]}2"),
                (Match.Stage.SF, "SF1", f"{g[0]}1", "WQF1"),
                (Match.Stage.SF, "SF2", f"{g[1]}1", "WQF2"),
                (Match.Stage.F,  "F1",  "WSF1",      "WSF2"),
            ]
        if N == 4:
            # Q=8, B=8 — 4 quarts + 2 demies + finale
            # Séparation maximale per spec :
            #   QF1=A1vsC2, QF2=D1vsB2, QF3=B1vsA2, QF4=C1vsD2
            return [
                (Match.Stage.QF, "QF1", f"{g[0]}1", f"{g[2]}2"),
                (Match.Stage.QF, "QF2", f"{g[3]}1", f"{g[1]}2"),
                (Match.Stage.QF, "QF3", f"{g[1]}1", f"{g[0]}2"),
                (Match.Stage.QF, "QF4", f"{g[2]}1", f"{g[3]}2"),
                (Match.Stage.SF, "SF1", "WQF1",      "WQF2"),
                (Match.Stage.SF, "SF2", "WQF3",      "WQF4"),
                (Match.Stage.F,  "F1",  "WSF1",      "WSF2"),
            ]
        return None  # N > 4 : non templé pour l'instant

    if qpg == 1:
        if N == 1:
            return []  # une seule poule, pas de phase finale
        if N == 2:
            # finale sèche
            return [
                (Match.Stage.F, "F1", f"{g[0]}1", f"{g[1]}1"),
            ]
        if N == 3:
            # Q=3, B=4, 1 bye (A1) — SF puis finale
            return [
                (Match.Stage.SF, "SF1", f"{g[1]}1", f"{g[2]}1"),
                (Match.Stage.F,  "F1",  f"{g[0]}1", "WSF1"),
            ]
        if N == 4:
            # Q=4, B=4 — 2 demies + finale (spec : A1 vs D1 / B1 vs C1)
            return [
                (Match.Stage.SF, "SF1", f"{g[0]}1", f"{g[3]}1"),
                (Match.Stage.SF, "SF2", f"{g[1]}1", f"{g[2]}1"),
                (Match.Stage.F,  "F1",  "WSF1",      "WSF2"),
            ]
        return None  # N > 4 : non templé pour l'instant

    return None


def ensure_final_bracket_exists(event):
    """
    Crée le squelette du tableau final selon le template positionnel
    (N groupes × qualified_per_group, avec byes et séparation maximale).
    """
    groups = list(Group.objects.filter(event=event).order_by("name"))
    N = len(groups)
    qpg = int(event.qualified_per_group or 0)
    if qpg <= 0 or N <= 0:
        return

    gnames = [g.name.upper() for g in groups]
    layout = _bracket_layout(gnames, qpg)
    if layout is None:
        return  # configuration non supportée

    def _rules_for_fmt(fmt):
        if fmt == Match.Format.QF_SET5_TB_5_5:
            return dict(games_to_win=6, tb_at=5, best_of=1)
        if fmt == Match.Format.NORMAL_1SET:
            return dict(games_to_win=6, tb_at=6, best_of=1)
        if fmt == Match.Format.BO3:
            return dict(games_to_win=6, tb_at=6, best_of=3)
        return dict(games_to_win=5, tb_at=4, best_of=1)

    for stage, slot, a_label, b_label in layout:
        fmt = _fmt_for_stage(stage)
        rules = _rules_for_fmt(fmt)
        m = Match.objects.filter(event=event, stage=stage, bracket_slot=slot).first()
        if m:
            if m.status == Match.Status.SCHEDULED:
                m.side_a_label = a_label
                m.side_b_label = b_label
                m.match_format = fmt
                m.games_to_win = rules["games_to_win"]
                m.tb_at = rules["tb_at"]
                m.best_of = rules["best_of"]
                m.tb_points_to_win = 7
                m.tb_win_by_two = True
                m.deciding_set_mode = Match.DecidingSetMode.FULL_SET
                m.deciding_tb_points_to_win = 10
                m.save(update_fields=[
                    "side_a_label", "side_b_label", "match_format",
                    "games_to_win", "tb_at", "best_of",
                    "tb_points_to_win", "tb_win_by_two",
                    "deciding_set_mode", "deciding_tb_points_to_win",
                ])
            continue

        Match.objects.create(
            edition=event.edition,
            event=event,
            stage=stage,
            bracket_slot=slot,
            match_format=fmt,
            games_to_win=rules["games_to_win"],
            tb_at=rules["tb_at"],
            best_of=rules["best_of"],
            tb_points_to_win=7,
            tb_win_by_two=True,
            deciding_set_mode=Match.DecidingSetMode.FULL_SET,
            deciding_tb_points_to_win=10,
            status=Match.Status.SCHEDULED,
            side_a=None,
            side_b=None,
            side_a_label=a_label,
            side_b_label=b_label,
        )

    # Slot P3 (petite finale) — créé seulement si l'épreuve le demande et qu'il y a au moins 2 SF
    sf_count = sum(1 for (stage, _, _, _) in layout if stage == Match.Stage.SF)
    if event.has_third_place and sf_count >= 2:
        fmt = _fmt_for_stage(Match.Stage.P3)
        rules = _rules_for_fmt(fmt)
        exists = Match.objects.filter(event=event, stage=Match.Stage.P3, bracket_slot="P3").exists()
        if not exists:
            Match.objects.create(
                edition=event.edition,
                event=event,
                stage=Match.Stage.P3,
                bracket_slot="P3",
                match_format=fmt,
                side_a_label="LSF1",
                side_b_label="LSF2",
                status=Match.Status.SCHEDULED,
                side_a=None,
                side_b=None,
                games_to_win=rules["games_to_win"],
                tb_at=rules["tb_at"],
                best_of=rules["best_of"],
                tb_points_to_win=7,
                tb_win_by_two=True,
                deciding_set_mode=Match.DecidingSetMode.FULL_SET,
                deciding_tb_points_to_win=10,
            )


def recreate_final_bracket_for_event(event, force=False):
    """
    Service réutilisable : (re)pose le squelette du tableau final dérivé des poules
    (même forme que ``ensure_final_bracket_exists`` — N poules × qualified_per_group,
    byes, séparation maximale).

    - Aucun tableau existant : régénère directement (``force`` sans effet).
    - Tableau existant, tous les matchs ``SCHEDULED``, ``force=False`` : no-op idempotent
      (délègue à ``ensure_final_bracket_exists``, comme l'appel initial au « Débuter »).
    - Tableau existant, tous les matchs ``SCHEDULED``, ``force=True`` : supprime les
      matchs du tableau puis régénère un squelette neuf.
    - Tableau existant avec au moins un match ``LIVE``/``FINISHED`` : toujours refusé
      (``ValueError``), que ``force`` soit vrai ou non.
    """
    existing = Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
    )

    if existing.exists():
        if existing.exclude(status=Match.Status.SCHEDULED).exists():
            raise ValueError("Impossible de recréer : un match est déjà en cours ou terminé.")
        if force:
            existing.delete()

    ensure_final_bracket_exists(event)


def sync_final_bracket_for_event(event):
    """
    Met à jour side_a/side_b dès que les ranks existent (labels positionnels : A1/B2/…).
    Ne touche pas les labels placeholder WQF*/WSF*.
    Ne crée pas le tableau — lecture seule des match slots existants.
    """
    qs = Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
        status=Match.Status.SCHEDULED,
    )

    for m in qs:
        changed = False

        if m.side_a is None and _is_group_label(m.side_a_label):
            ea = _resolve_label_to_entry(event, m.side_a_label)
            if ea is not None:
                m.side_a = ea
                changed = True

        if m.side_b is None and _is_group_label(m.side_b_label):
            eb = _resolve_label_to_entry(event, m.side_b_label)
            if eb is not None:
                m.side_b = eb
                changed = True

        if changed:
            m.save(update_fields=["side_a", "side_b"])


def _winner_entry(match):
    if match.status != Match.Status.FINISHED:
        return None
    if match.winner_side == "A":
        return match.side_a
    if match.winner_side == "B":
        return match.side_b
    return None


def _loser_entry(match):
    if match.status != Match.Status.FINISHED:
        return None
    if match.winner_side == "A":
        return match.side_b
    if match.winner_side == "B":
        return match.side_a
    return None


def _slot_num(slot: str, prefix: str):
    if not slot:
        return None
    slot = slot.upper()
    if not slot.startswith(prefix):
        return None
    num = slot[len(prefix):]
    return num if num.isdigit() else None


def sync_final_winners_for_event(event):
    """
    Propage les vainqueurs (QF → SF → F) en se basant sur les labels WQF*/WSF*.
    Ne touche pas les labels positionnels (A1/B2…) — gérés par sync_final_bracket_for_event.
    """
    qf = list(Match.objects.filter(event=event, stage=Match.Stage.QF))
    sf = list(Match.objects.filter(event=event, stage=Match.Stage.SF))

    winners = {}
    for m in qf:
        n = _slot_num(m.bracket_slot, "QF")
        if not n:
            continue
        w = _winner_entry(m)
        if w:
            winners[f"WQF{n}"] = w

    for m in sf:
        n = _slot_num(m.bracket_slot, "SF")
        if not n:
            continue
        w = _winner_entry(m)
        if w:
            winners[f"WSF{n}"] = w

    targets = Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.SF, Match.Stage.F],
        status=Match.Status.SCHEDULED,
    )

    default_source_by_slot_side = {
        ("SF1", "A"): "WQF1",
        ("SF1", "B"): "WQF2",
        ("SF2", "A"): "WQF3",
        ("SF2", "B"): "WQF4",
        ("F1", "A"): "WSF1",
        ("F1", "B"): "WSF2",
    }

    for m in targets:
        changed = False
        la = (m.side_a_label or "").upper().strip()
        lb = (m.side_b_label or "").upper().strip()

        if not la:
            la = default_source_by_slot_side.get((m.bracket_slot or "", "A"), "")
        if not lb:
            lb = default_source_by_slot_side.get((m.bracket_slot or "", "B"), "")

        if m.side_a is None and la.startswith("W") and la in winners:
            m.side_a = winners[la]
            changed = True
        if m.side_b is None and lb.startswith("W") and lb in winners:
            m.side_b = winners[lb]
            changed = True

        if changed:
            m.save(update_fields=["side_a", "side_b"])


def sync_p3_losers_for_event(event):
    """
    Propage les perdants de SF1/SF2 vers le slot P3.
    N'agit que si event.has_third_place et si un slot P3 SCHEDULED existe.
    """
    if not event.has_third_place:
        return
    p3 = Match.objects.filter(
        event=event,
        stage=Match.Stage.P3,
        bracket_slot="P3",
        status=Match.Status.SCHEDULED,
    ).first()
    if not p3:
        return
    sf_matches = {
        m.bracket_slot: m
        for m in Match.objects.filter(event=event, stage=Match.Stage.SF)
    }
    changed = False
    if p3.side_a is None:
        sf1 = sf_matches.get("SF1")
        if sf1:
            loser = _loser_entry(sf1)
            if loser:
                p3.side_a = loser
                changed = True
    if p3.side_b is None:
        sf2 = sf_matches.get("SF2")
        if sf2:
            loser = _loser_entry(sf2)
            if loser:
                p3.side_b = loser
                changed = True
    if changed:
        p3.save(update_fields=["side_a", "side_b"])

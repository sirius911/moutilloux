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


def ensure_final_bracket_exists(event):
    """
    Crée le squelette du tableau final (même si poules pas finies)
    Hypothèses:
      - qualified_per_group == 2 (A1/A2 ...)
      - 4 poules A/B/C/D => QF1..QF4 + SF + F
      - 2 poules A/B     => SF1..SF2 + F
      - 3 poules A/B/C   => tableau à 6 :
            QF1: S3 vs S6
            QF2: S4 vs S5
            SF1: S1 vs WQF2
            SF2: S2 vs WQF1
            F1 : WSF1 vs WSF2
        où S1..S6 sont des "seeds" globaux (remplis plus tard par sync)
    """
    groups = list(Group.objects.filter(event=event).order_by("name"))
    if int(event.qualified_per_group or 0) != 2:
        return

    names = {g.name.upper() for g in groups}

    def _rules_for_fmt(fmt):
        if fmt == Match.Format.QF_SET5_TB_5_5:
            return dict(games_to_win=6, tb_at=5, best_of=1)
        if fmt == Match.Format.NORMAL_1SET:
            return dict(games_to_win=6, tb_at=6, best_of=1)
        if fmt == Match.Format.BO3:
            return dict(games_to_win=6, tb_at=6, best_of=3)
        return dict(games_to_win=5, tb_at=4, best_of=1)

    def get_or_create(stage, slot, a_label, b_label, fmt):
        rules = _rules_for_fmt(fmt)
        m = Match.objects.filter(event=event, stage=stage, bracket_slot=slot).first()
        if m:
            # on met à jour seulement si match pas lancé
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
            return

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

    # ---- 4 poules : quarts (4), demies (2), finale (1)
    if len(groups) == 4 and {"A", "B", "C", "D"} <= names:
        get_or_create(Match.Stage.QF, "QF1", "A1", "D2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF2", "C1", "B2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF3", "B1", "C2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF4", "D1", "A2", Match.Format.QF_SET5_TB_5_5)

        get_or_create(Match.Stage.SF, "SF1", "WQF1", "WQF2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.SF, "SF2", "WQF3", "WQF4", Match.Format.NORMAL_1SET)

        get_or_create(Match.Stage.F, "F1", "WSF1", "WSF2", Match.Format.BO3)
        return

    # ---- 2 poules : demies (2), finale (1)
    if len(groups) == 2 and {"A", "B"} <= names:
        get_or_create(Match.Stage.SF, "SF1", "A1", "B2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.SF, "SF2", "B1", "A2", Match.Format.NORMAL_1SET)

        get_or_create(Match.Stage.F, "F1", "WSF1", "WSF2", Match.Format.BO3)
        return

    # ---- 3 poules : tableau à 6 (2 quarts, 2 demies, 1 finale)
    if len(groups) == 3 and {"A", "B", "C"} <= names:
        # Tableau à 6 => 2 quarts, 2 demies, 1 finale
        # (S1..S6 seront résolus par sync, pour l’instant on crée juste le squelette)

        # Quarts
        get_or_create(Match.Stage.QF, "QF1", "S3", "S6", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF2", "S4", "S5", Match.Format.QF_SET5_TB_5_5)

        # Demies (2 têtes de série avec bye)
        get_or_create(Match.Stage.SF, "SF1", "S1", "WQF2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.SF, "SF2", "S2", "WQF1", Match.Format.NORMAL_1SET)

        # Finale
        get_or_create(Match.Stage.F, "F1", "WSF1", "WSF2", Match.Format.BO3)

    # autres cas non gérés
    return


def _is_group_label(label: str) -> bool:
    # A1, B2, C1, D2...
    if not label or len(label) < 2:
        return False
    if not label[0].isalpha():
        return False
    return label[1:].isdigit()


def _is_seed_label(label: str) -> bool:
    # S1..S6
    if not label or len(label) < 2:
        return False
    if label[0].upper() != "S":
        return False
    return label[1:].isdigit()


def sync_final_bracket_for_event(event):
    """
    Met à jour side_a/side_b dès que les ranks existent.
    IMPORTANT: on ne crée PAS le tableau automatiquement.
    On ne remplit que les cases vides, tant que le match n’a pas démarré
    (status=SCHEDULED), pour éviter d’écraser un remplissage manuel.

    Gère:
      - labels de poule: A1/B2/C1...
      - labels seeds (3 poules): S1..S6 (classement global)
      - ne touche pas aux labels placeholder WQF1/WSF1...
    """
    # --- Pré-calcul des seeds S1..S6 si on a 3 poules (A/B/C)
    seed_map = {}  # "S1" -> Entry, ...
    groups = list(Group.objects.filter(event=event).order_by("name"))
    names = {g.name.upper() for g in groups}

    if len(groups) == 3 and {"A", "B", "C"} <= names:
        # ex: ["A1","C1","B1","A2","C2","B2"] triés globalement
        seed_labels = _seed_labels_for_3_groups(event)  # déjà dans ton fichier
        # seed_labels est trié du meilleur au moins bon
        for i, lab in enumerate(seed_labels[:6], start=1):
            entry = _resolve_label_to_entry(event, lab)  # lab = "A1"/"B2"/...
            if entry:
                seed_map[f"S{i}"] = entry

    qs = Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
        status=Match.Status.SCHEDULED,
    )

    for m in qs:
        changed = False

        # --- side A
        if m.side_a is None:
            if _is_group_label(m.side_a_label):
                ea = _resolve_label_to_entry(event, m.side_a_label)
                if ea is not None:
                    m.side_a = ea
                    changed = True
            elif _is_seed_label(m.side_a_label):
                ea = seed_map.get(m.side_a_label.upper())
                if ea is not None:
                    m.side_a = ea
                    changed = True

        # --- side B
        if m.side_b is None:
            if _is_group_label(m.side_b_label):
                eb = _resolve_label_to_entry(event, m.side_b_label)
                if eb is not None:
                    m.side_b = eb
                    changed = True
            elif _is_seed_label(m.side_b_label):
                eb = seed_map.get(m.side_b_label.upper())
                if eb is not None:
                    m.side_b = eb
                    changed = True

        # On ne touche pas aux labels type WSF1/WQF1 etc : placeholder
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
    Propage automatiquement les vainqueurs (QF -> SF, SF -> F)
    en se basant sur les labels WQF1/WSF1, sans écraser un choix manuel.
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

    # Fallback standard mapping si labels WQF*/WSF* absents
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

        if m.side_a is None and la in winners:
            m.side_a = winners[la]
            changed = True
        if m.side_b is None and lb in winners:
            m.side_b = winners[lb]
            changed = True

        if changed:
            m.save(update_fields=["side_a", "side_b"])


def _seed_entries_for_3_groups(event):
    """
    Retourne une liste de tuples (label, entry_id) triée du seed1 au seed6.
    On compare sur les standings de poule (points, games_won, diff).
    """
    groups = list(Group.objects.filter(event=event).order_by("name"))
    labels = []
    for g in groups:
        labels.append(f"{g.name.upper()}1")
        labels.append(f"{g.name.upper()}2")

    items = []
    for lab in labels:
        e = _resolve_label_to_entry(event, lab)
        if not e:
            continue
        # standing de l'entry dans SA poule
        st = (GroupStanding.objects
              .filter(entry=e, group__event=event)
              .values("points", "games_won", "games_lost")
              .first())
        if not st:
            continue

        points = st["points"] or 0
        gw = st["games_won"] or 0
        gl = st["games_lost"] or 0
        diff = gw - gl
        items.append((lab, e, points, gw, diff))

    # tri global (seed1 = meilleur)
    items.sort(key=lambda x: (x[2], x[3], x[4]), reverse=True)
    # retourne seed list : [(label, entry), ...]
    return [(lab, e) for lab, e, *_ in items]


def _standing_key_for_entry(event, entry):
    st = (
        GroupStanding.objects
        .filter(entry=entry, group__event=event)
        .values("points", "games_won", "games_lost")
        .first()
    )
    if not st:
        return None
    points = st["points"] or 0
    gw = st["games_won"] or 0
    gl = st["games_lost"] or 0
    diff = gw - gl
    return (points, gw, diff)


def _seed_labels_for_3_groups(event):
    """
    Retourne une liste de 6 labels triés du seed1 au seed6.
    Labels attendus: A1,A2,B1,B2,C1,C2 (selon poules existantes).
    Tri global : points, games_won, diff.
    Ne garde que les labels dont l'entry est déjà résoluble (rank dispo).
    """
    groups = list(Group.objects.filter(event=event).order_by("name"))
    labels = []
    for g in groups:
        gname = g.name.upper()
        labels.append(f"{gname}1")
        labels.append(f"{gname}2")

    items = []
    for lab in labels:
        entry = _resolve_label_to_entry(event, lab)  # tu l'as déjà
        if not entry:
            continue
        key = _standing_key_for_entry(event, entry)
        if not key:
            continue
        items.append((lab, entry, key))

    items.sort(key=lambda x: x[2], reverse=True)
    return [lab for lab, entry, key in items]

from collections import defaultdict
from competition.models import GroupStanding, GroupMembership
from live.models import Match
from live.bracket import group_is_finished


def get_hero_match(edition):
    return (
        Match.objects.filter(edition=edition, status=Match.Status.LIVE)
        .select_related("event", "event__category", "court", "side_a", "side_b")
        .order_by("-is_featured", "-updated_at")
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
                    if s.rank and s.rank <= ev.qualified_per_group and group_is_finished(g):
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

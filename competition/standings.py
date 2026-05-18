from django.db import transaction
from django.db.models import Q

from competition.models import GroupStanding, GroupMembership
from live.models import Match


@transaction.atomic
def recalc_one_group(group_id: int) -> None:
    # Entries de la poule
    entries = list(
        GroupMembership.objects.filter(group_id=group_id).values_list("entry_id", flat=True)
    )

    # Assurer une ligne standing par entry
    for entry_id in entries:
        GroupStanding.objects.get_or_create(group_id=group_id, entry_id=entry_id)

    # Reset stats
    GroupStanding.objects.filter(group_id=group_id).update(
        wins=0, losses=0, points=0, games_won=0, games_lost=0, rank=None
    )

    standings = {
        s.entry_id: s
        for s in GroupStanding.objects.select_for_update().filter(group_id=group_id)
    }

    # Matches terminés de la poule
    matches = Match.objects.filter(
        group_id=group_id,
        stage=Match.Stage.GROUP,
        status=Match.Status.FINISHED,
    ).filter(
        Q(side_a_id__in=entries) & Q(side_b_id__in=entries)
    )

    for m in matches:
        a = standings.get(m.side_a_id)
        b = standings.get(m.side_b_id)
        if not a or not b:
            continue

        # Jeux
        a.games_won += m.games_a
        a.games_lost += m.games_b
        b.games_won += m.games_b
        b.games_lost += m.games_a

        # Victoire / défaite
        if m.games_a > m.games_b:
            a.wins += 1
            b.losses += 1
        elif m.games_b > m.games_a:
            b.wins += 1
            a.losses += 1
        else:
            continue

    # Points = 2 par victoire
    for s in standings.values():
        s.points = s.wins * 2
        s.save()

    # Classement
    ordered = sorted(
        standings.values(),
        key=lambda s: (s.points, s.games_won, (s.games_won - s.games_lost)),
        reverse=True
    )
    for idx, s in enumerate(ordered, start=1):
        s.rank = idx
        s.save(update_fields=["rank"])

    # ✅ ICI : après que les ranks sont en base
    from competition.models import Group
    from live.bracket import sync_final_bracket_for_event

    group = Group.objects.select_related("event").get(id=group_id)
    sync_final_bracket_for_event(group.event)


def recalc_event_groups(event_id: int) -> None:
    # Groupes ayant au moins un match de poule terminé
    group_ids = (
        Match.objects.filter(
            event_id=event_id,
            stage=Match.Stage.GROUP,
            status=Match.Status.FINISHED,
            group__isnull=False,
        )
        .values_list("group_id", flat=True)
        .distinct()
    )

    for gid in group_ids:
        recalc_one_group(gid)

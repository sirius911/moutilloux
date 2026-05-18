from django.core.management.base import BaseCommand
from competition.standings import recalc_one_group, recalc_event_groups
from live.models import Match


class Command(BaseCommand):
    help = "Recalcule les classements (standings) de toutes les poules à partir des matchs terminés."

    def add_arguments(self, parser):
        parser.add_argument("--event-id", type=int, default=None)

    def handle(self, *args, **options):
        event_id = options["event_id"]

        if event_id is not None:
            recalc_event_groups(event_id)
            self.stdout.write(self.style.SUCCESS("Classements recalculés."))
            return

        # Sinon : tous events
        group_ids = (
            Match.objects.filter(stage=Match.Stage.GROUP, status=Match.Status.FINISHED, group__isnull=False)
            .values_list("group_id", flat=True)
            .distinct()
        )
        if not group_ids:
            self.stdout.write(self.style.WARNING("Aucun match de poule terminé trouvé."))
            return

        for gid in group_ids:
            recalc_one_group(gid)

        self.stdout.write(self.style.SUCCESS("Classements recalculés."))

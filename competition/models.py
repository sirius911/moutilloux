from django.db import models
from django.core.exceptions import ValidationError
from core.models import TournamentEdition, Player, Team


class Category(models.Model):
    """
    "Simple homme", "Double mixte", "Junior", etc.
    """
    class Mode(models.TextChoices):
        SINGLE = "S", "Simple"
        DOUBLE = "D", "Double"

    name = models.CharField(max_length=120, unique=True)
    mode = models.CharField(max_length=1, choices=Mode.choices)

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    """
    Une catégorie dans une édition : ex "Double mixte" pour 2026.
    """
    edition = models.ForeignKey(TournamentEdition, on_delete=models.CASCADE, related_name="events")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="events")

    # configuration "année par année"
    group_size_default = models.PositiveIntegerField(default=4)  # 3 ou 4 en général
    qualified_per_group = models.PositiveIntegerField(default=2)  # 1 ou 2
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("edition", "category")]
        ordering = ["edition__year", "category__name"]

    def __str__(self) -> str:
        return f"{self.category} - {self.edition.year}"


class Entry(models.Model):
    """
    Une participation à un Event.
    - en simple: player renseigné
    - en double: team renseigné
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="entries")

    player = models.ForeignKey(Player, on_delete=models.PROTECT, null=True, blank=True, related_name="entries")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, blank=True, related_name="entries")

    seed_hint = models.PositiveIntegerField(null=True, blank=True)  # optionnel (si un jour tu veux "têtes de série")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(player__isnull=False) & models.Q(team__isnull=True))
                    | (models.Q(player__isnull=True) & models.Q(team__isnull=False))
                ),
                name="entry_requires_player_xor_team",
            )
        ]

    def clean(self):
        # cohérence avec le mode de catégorie
        mode = self.event.category.mode
        if mode == Category.Mode.SINGLE and self.player is None:
            raise ValidationError("Cette catégorie est en simple : il faut un joueur.")
        if mode == Category.Mode.DOUBLE and self.team is None:
            raise ValidationError("Cette catégorie est en double : il faut une équipe.")

    def __str__(self) -> str:
        return str(self.player or self.team)


class Group(models.Model):
    """
    Poule A, B, C...
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=10)  # "A", "B", "C", "D" ou "P1" etc.

    class Meta:
        unique_together = [("event", "name")]
        ordering = ["event_id", "name"]

    def __str__(self) -> str:
        return f"Poule {self.name} ({self.event})"

    def expected_group_match_count(self) -> int:
        """
        Nombre de matchs attendus en round-robin simple pour cette poule.
        N équipes => N*(N-1)/2
        """
        n = self.memberships.count()
        return (n * (n - 1)) // 2

    def all_group_matches_finished(self) -> bool:
        """
        True si tous les matchs de poule attendus existent et sont FINISHED.
        (Strict : total == expected et finished == expected)
        """
        from live.models import Match  # import local pour éviter circular import

        expected = self.expected_group_match_count()
        if expected == 0:
            return True  # 0 ou 1 équipe => rien à jouer

        qs = Match.objects.filter(group=self, stage=Match.Stage.GROUP)
        total = qs.count()
        finished = qs.filter(status__in=[Match.Status.FINISHED, Match.Status.CANCELED]).count()

        return total == expected and finished == expected

    def ready_for_qualification(self) -> bool:
        """
        True si la poule est finie ET si les rangs sont calculés
        pour les qualifiés requis (ex: A1/A2).
        """
        if not self.all_group_matches_finished():
            return False

        q = int(self.event.qualified_per_group or 0)
        if q <= 0:
            return False

        # On vérifie qu'on a bien au moins q standings avec rank non null (1..q)
        ranked = self.standings.filter(rank__isnull=False, rank__lte=q).count()
        return ranked >= q

    def qualified_entries(self):
        """
        Retourne la liste des Entry qualifiées (A1, A2, ...) dans l'ordre des ranks.
        Retourne [] si pas prêt.
        """
        if not self.ready_for_qualification():
            return []

        q = int(self.event.qualified_per_group or 0)
        return [
            s.entry
            for s in self.standings.select_related("entry")
            .filter(rank__isnull=False, rank__lte=q)
            .order_by("rank")
        ]


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="group_memberships")

    class Meta:
        unique_together = [("group", "entry")]

    def __str__(self) -> str:
        return f"{self.entry} in {self.group}"


class GroupStanding(models.Model):
    """
    Stats calculées (on remplira ça plus tard automatiquement).
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="standings")
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="standings")

    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)  # wins * 2
    games_won = models.PositiveIntegerField(default=0)
    games_lost = models.PositiveIntegerField(default=0)

    # rang final dans la poule (1,2,3,4)
    rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("group", "entry")]
        ordering = ["group_id", "rank", "-points", "-games_won"]

    def __str__(self) -> str:
        return f"{self.group} - {self.entry} (pts:{self.points})"

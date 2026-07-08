from django.db import models, transaction


class TournamentEdition(models.Model):
    name = models.CharField(max_length=120)  # ex: "Tournois des Moutilloux 2026"
    year = models.PositiveIntegerField(db_index=True, unique=True)
    start_dt = models.DateTimeField(null=True, blank=True)
    end_dt = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    default_match_duration_min = models.PositiveSmallIntegerField(default=27)

    class Meta:
        ordering = ["-year"]

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_active:
                TournamentEdition.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
            super().save(*args, **kwargs)


class Player(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Homme"
        FEMALE = "F", "Femme"
        OTHER = "O", "Autre"

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True, default="")
    birth_year = models.PositiveIntegerField(null=True, blank=True)

    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    license_number = models.CharField(max_length=50, blank=True, default="", db_index=True)

    photo = models.ImageField(upload_to="players/", null=True, blank=True)
    attitude = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()


class Team(models.Model):
    """
    Une équipe pour les doubles.
    On garde volontairement un nom optionnel, et 2 joueurs.
    """
    name = models.CharField(max_length=120, blank=True, default="")
    player1 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="teams_as_p1")
    player2 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="teams_as_p2")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(player1=models.F("player2")),
                name="team_players_must_be_different",
            )
        ]

    def __str__(self) -> str:
        if self.name:
            return self.name
        return f"{self.player1} / {self.player2}"


def get_current_edition():
    return (
        TournamentEdition.objects.filter(is_active=True).order_by("-year").first()
        or TournamentEdition.objects.order_by("-year").first()
    )

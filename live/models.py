from django.db import models, transaction
from django.utils import timezone
from core.models import TournamentEdition
from competition.models import Event, Group, Entry
import datetime


class Court(models.Model):
    name = models.CharField(max_length=50, unique=True)  # ex "Court 1", "Central", etc.

    def __str__(self) -> str:
        return self.name


class Match(models.Model):
    class Stage(models.TextChoices):
        GROUP = "GROUP", "Poule"
        QF = "QF", "Quart"
        SF = "SF", "Demi"
        F = "F", "Finale"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Planifié"
        LIVE = "LIVE", "En cours"
        FINISHED = "FINISHED", "Terminé"
        CANCELED = "CANCELED", "Annulé"

    class Format(models.TextChoices):
        GROUP_SET5_TB_4_4 = "G_SET5_TB44", "Poule: 1 set à 5, TB à 4-4"
        QF_SET5_TB_5_5 = "QF_SET5_TB55", "Quart: 1 set à 6, TB à 5-5"
        NORMAL_1SET = "NORMAL_1SET", "Demi: 1 set normal"
        BO3 = "BO3", "Finale: 2 sets gagnants"
        MANUAL = "MANUAL", "Manuel (aucune règle auto)"

    edition = models.ForeignKey(TournamentEdition, on_delete=models.CASCADE, db_index=True)

    # --- Règles de score (modulables) ---
    games_to_win = models.PositiveSmallIntegerField(default=5)     # ex: 5 (poule) ou 6 (normal)
    tb_at = models.PositiveSmallIntegerField(default=4)            # ex: 4-4 (poule), 6-6 (normal)
    best_of = models.PositiveSmallIntegerField(default=1)          # 1 (1 set) ou 3 (2 sets gagnants)

    tb_points_to_win = models.PositiveSmallIntegerField(default=7)  # TB classique à 7
    tb_win_by_two = models.BooleanField(default=True)              # 2 points d'écart
    class DecidingSetMode(models.TextChoices):
        FULL_SET = "FULL_SET", "Set décisif normal"
        SUPER_TB = "SUPER_TB", "Super tie-break décisif"

    deciding_set_mode = models.CharField(
        max_length=12,
        choices=DecidingSetMode.choices,
        default=DecidingSetMode.FULL_SET,
    )
    deciding_tb_points_to_win = models.PositiveSmallIntegerField(default=10)
    set_scores = models.JSONField(default=list, blank=True)

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="matches")

    # Poule (si match de poule)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")

    stage = models.CharField(max_length=10, choices=Stage.choices, db_index=True)
    match_format = models.CharField(max_length=20, choices=Format.choices, db_index=True)

    # Participants
    side_a = models.ForeignKey(Entry, on_delete=models.PROTECT, related_name="matches_as_a", null=True, blank=True)
    side_b = models.ForeignKey(Entry, on_delete=models.PROTECT, related_name="matches_as_b", null=True, blank=True)

    side_a_label = models.CharField(max_length=20, null=True, blank=True)  # ex: "A1"
    side_b_label = models.CharField(max_length=20, null=True, blank=True)  # ex: "D2"

    # Planning
    scheduled_time = models.DateTimeField(null=True, blank=True)
    court = models.ForeignKey(Court, on_delete=models.SET_NULL, null=True, blank=True)
    order_index = models.PositiveIntegerField(null=True, blank=True)

    # Live/status
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)  # "match en cours" affichage public

    # Score (MVP simple)
    # sets gagnés
    sets_a = models.PositiveIntegerField(default=0)
    sets_b = models.PositiveIntegerField(default=0)

    # jeux dans le set en cours
    games_a = models.PositiveIntegerField(default=0)
    games_b = models.PositiveIntegerField(default=0)

    # tiebreak (si actif)
    tb_active = models.BooleanField(default=False)
    tb_points_a = models.PositiveIntegerField(default=0)
    tb_points_b = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    bracket_slot = models.CharField(max_length=10, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["event_id", "scheduled_time", "order_index", "id"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(side_a__isnull=True) |
                    models.Q(side_b__isnull=True) |
                    ~models.Q(side_a=models.F("side_b"))
                ),
                name="match_sides_must_be_different",
            ),

            models.UniqueConstraint(
                fields=["edition", "order_index"],
                name="uniq_order_per_edition",
            ),
            models.CheckConstraint(
                check=models.Q(order_index__isnull=True) | models.Q(court__isnull=False),
                name="court_required_when_ordered",
            ),
            models.UniqueConstraint(
                fields=["event", "stage", "bracket_slot"],
                name="uniq_bracket_slot_per_stage_event",
            ),
            models.CheckConstraint(
                check=(
                    ~models.Q(stage="GROUP") |
                    (models.Q(side_a__isnull=False) & models.Q(side_b__isnull=False))
                ),
                name="group_matches_require_sides",
            ),
        ]

    class WinnerSide(models.TextChoices):
        A = "A", "A"
        B = "B", "B"

    winner_side = models.CharField(max_length=1, choices=WinnerSide.choices, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.event}: {self.side_a} vs {self.side_b}"

    def mark_live(self):
        with transaction.atomic():
            # désactive tous les autres LIVE de la même édition
            Match.objects.filter(edition=self.edition, status=Match.Status.LIVE).exclude(pk=self.pk)\
                .update(status=Match.Status.SCHEDULED)

            self.status = Match.Status.LIVE
            # quand un match devient LIVE, il sort de la file
            self.order_index = None

            if not self.started_at:
                self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at", "order_index"])

    def mark_finished(self):
        self.status = Match.Status.FINISHED
        if not self.finished_at:
            self.finished_at = timezone.now()

    class Server(models.TextChoices):
        A = "A", "A sert"
        B = "B", "B sert"

    server = models.CharField(max_length=1, choices=Server.choices, default=Server.A)

    # points du jeu en cours (brut, pas 15/30/40)
    points_a = models.PositiveSmallIntegerField(default=0)
    points_b = models.PositiveSmallIntegerField(default=0)

    def tennis_point_display(self):
        """
            Retourne (display_a, display_b) au format tennis (0,15,30,40,AV)
            en gérant le deuce/avantage.
        """
        a = int(self.points_a or 0)
        b = int(self.points_b or 0)

        # cas standard avant deuce
        mapping = {0: "0", 1: "15", 2: "30", 3: "40"}

        # si aucun n'a atteint 3 points (40), mapping simple
        if a <= 3 and b <= 3 and not (a == 3 and b == 3):
            return mapping.get(a, "40"), mapping.get(b, "40")

        # deuce et avantage : à partir de 40-40 (3-3) et au-delà
        if a == b:
            return "40", "40"

        if a > b:
            # A a l'avantage si l'écart est 1, sinon (écart >=2) match game (géré ailleurs)
            return "AV", "40" if b >= 3 else "40"
        else:
            return "40" if a >= 3 else "40", "AV"

    def save(self, *args, **kwargs):
        if self.event_id:
            self.edition = self.event.edition

        # ✅ Fix: si une heure a été saisie sans date -> Django l’a mise au 01/01/1900
        if self.scheduled_time and self.scheduled_time.year == 1900:
            tz = timezone.get_current_timezone()

            # On prend l'heure en "local"
            st_local = timezone.localtime(self.scheduled_time, tz)
            t = st_local.time().replace(tzinfo=None)

            # On colle cette heure sur la date du jour (local)
            d = timezone.localdate()
            new_local_dt = datetime.datetime.combine(d, t)

            # On re-rend aware puis on stocke
            self.scheduled_time = timezone.make_aware(new_local_dt, tz)

        # si on ordonne un match et qu'il n'a pas de court, on met "Central" (si unique court)
        if self.order_index is not None and self.court_id is None:
            central = Court.objects.filter(name="Central").first()
            if central:
                self.court = central

        # ✅ Si le match passe LIVE : started_at doit être défini
        if self.status == Match.Status.LIVE and self.started_at is None:
            self.started_at = timezone.now()

        # ✅ Si le match redevient SCHEDULED : (optionnel) on remet started_at à None
        # (utile si on a mis LIVE par erreur)
        if self.status == Match.Status.SCHEDULED:
            # option soft : on ne reset que si le match n'a pas vraiment commencé
            # ou si tu veux toujours reset, décommente la ligne suivante
            # self.started_at = None
            pass

        # ✅ Si le match est FINISHED : finished_at doit être défini
        if self.status == Match.Status.FINISHED and self.finished_at is None:
            self.finished_at = timezone.now()

        super().save(*args, **kwargs)

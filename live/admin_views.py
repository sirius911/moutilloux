import random
import json
import datetime
from collections import defaultdict
from django.contrib import messages

from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from core.models import TournamentEdition, Player, Team
from competition.models import Category, Event, Entry, Group, GroupMembership, GroupStanding
from live.models import Match, Court, PlayDay, Break
from live.views import build_event_group_tables

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def panel_counts(event):
    return {
        "entry_count": Entry.objects.filter(event=event).count(),
        "group_count": Group.objects.filter(event=event).count(),
        "match_count": Match.objects.filter(event=event).count(),
    }


def superuser_required(view):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser)(view)


# -----------------------
# Forms
# -----------------------

class SelectEventForm(forms.Form):
    edition = forms.ModelChoiceField(queryset=TournamentEdition.objects.order_by("-year"))
    event = forms.ModelChoiceField(queryset=Event.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # si edition pré-sélectionnée, filtre les events
        if "edition" in self.data:
            try:
                edition_id = int(self.data.get("edition"))
                self.fields["event"].queryset = Event.objects.filter(edition_id=edition_id).select_related("category")
            except Exception:
                pass
        elif self.initial.get("edition"):
            edition = self.initial["edition"]
            self.fields["event"].queryset = Event.objects.filter(edition=edition).select_related("category")


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["first_name", "last_name", "gender", "birth_year", "phone", "email", "license_number"]
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "gender": "Sexe",
            "birth_year": "Année de naissance",
            "phone": "Téléphone",
            "email": "Email",
            "license_number": "Numéro de licence",
        }


class TeamForm(forms.Form):
    name = forms.CharField(required=False)
    player1 = forms.ModelChoiceField(queryset=Player.objects.order_by("last_name", "first_name"))
    player2 = forms.ModelChoiceField(queryset=Player.objects.order_by("last_name", "first_name"))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("player1") == cleaned.get("player2"):
            raise forms.ValidationError("Les deux joueurs doivent être différents.")
        return cleaned


class GroupCreateForm(forms.Form):
    name = forms.CharField(max_length=10, help_text="Ex: A, B, C...")


class GroupFillForm(forms.Form):
    shuffle = forms.BooleanField(required=False, initial=True, help_text="Mélanger les participants")
    group_size = forms.ChoiceField(choices=[(3, "3"), (4, "4")], initial=4)
    # nb poules optionnel : sinon auto
    num_groups = forms.IntegerField(required=False, min_value=1, help_text="Optionnel. Sinon auto.")


class MatchEditForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            # Gestion
            "status", "scheduled_time", "court", "order_index",

            # Règles modulables
            "match_format", "games_to_win", "tb_at", "best_of",
            "tb_points_to_win", "tb_win_by_two",
            "deciding_set_mode", "deciding_tb_points_to_win",

            # Score
            "server", "points_a", "points_b",
            "sets_a", "sets_b", "games_a", "games_b",
            "tb_active", "tb_points_a", "tb_points_b",
            "winner_side",
        ]
        labels = {
            # Gestion
            "status": "Statut",
            "scheduled_time": "Heure prévue",
            "court": "Court",
            "order_index": "Ordre (file)",

            # Règles
            "match_format": "Format (preset)",
            "games_to_win": "Jeux pour gagner le set",
            "tb_at": "Tie-break à (ex: 6 pour 6-6)",
            "best_of": "Format (BO)",
            "tb_points_to_win": "Points pour gagner le tie-break",
            "tb_win_by_two": "Tie-break : 2 points d’écart",
            "deciding_set_mode": "Set décisif (si égalité en sets)",
            "deciding_tb_points_to_win": "Points du super tie-break décisif",

            # Score
            "server": "Service",
            "points_a": "Points (A)",
            "points_b": "Points (B)",
            "sets_a": "Sets (A)",
            "sets_b": "Sets (B)",
            "games_a": "Jeux (A)",
            "games_b": "Jeux (B)",
            "tb_active": "Tie-break en cours",
            "tb_points_a": "Points TB (A)",
            "tb_points_b": "Points TB (B)",
            "winner_side": "Vainqueur",
        }
        help_texts = {
            "order_index": "Laisse vide si le match n’est pas dans la liste ordonnée.",
            "best_of": "1 = 1 set (poule/quart/demi), 3 = 2 sets gagnants (finale).",
            "tb_at": "Ex: 4 => TB à 4-4 ; 6 => TB à 6-6 ; 5 => TB à 5-5.",
            "deciding_tb_points_to_win": "Utilisé seulement si set décisif en super tie-break.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        inst = self.instance
        if inst and inst.pk and inst.status == Match.Status.LIVE:
            # En LIVE : on évite de casser les règles en cours
            for f in ["match_format", "games_to_win", "tb_at", "best_of", "tb_points_to_win", "tb_win_by_two"]:
                if f in self.fields:
                    self.fields[f].disabled = True
                    self.fields[f].help_text = (self.fields[f].help_text or "") +\
                        " (verrouillé pendant un match en cours)"

        # Petites contraintes d'UI
        if "games_to_win" in self.fields:
            self.fields["games_to_win"].min_value = 1
            self.fields["games_to_win"].max_value = 9

        if "tb_at" in self.fields:
            self.fields["tb_at"].min_value = 0
            self.fields["tb_at"].max_value = 9

        if "best_of" in self.fields:
            self.fields["best_of"].min_value = 1
            self.fields["best_of"].max_value = 5

        if "tb_points_to_win" in self.fields:
            self.fields["tb_points_to_win"].min_value = 1
            self.fields["tb_points_to_win"].max_value = 50

        if "scheduled_time" in self.fields:
            self.fields["scheduled_time"].widget = forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"}
            )
            self.fields["scheduled_time"].input_formats = ["%H:%M", "%H:%M:%S"]

        if "order_index" in self.fields:
            self.fields["order_index"].disabled = True
            self.fields["order_index"].help_text = "Géré dans le panel Matchs."

    def clean(self):
        cleaned = super().clean()
        inst = self.instance
        fmt = cleaned.get("match_format")

        # Ne pas appliquer de preset si match en cours
        if inst and inst.pk and inst.status == Match.Status.LIVE:
            return cleaned

        PRESETS = {
            Match.Format.GROUP_SET5_TB_4_4: dict(
                games_to_win=5, tb_at=4, best_of=1,
                tb_points_to_win=7, tb_win_by_two=True
            ),
            Match.Format.QF_SET5_TB_5_5: dict(
                games_to_win=6, tb_at=5, best_of=1,
                tb_points_to_win=7, tb_win_by_two=True
            ),
            Match.Format.NORMAL_1SET: dict(
                games_to_win=6, tb_at=6, best_of=1,
                tb_points_to_win=7, tb_win_by_two=True
            ),
            Match.Format.BO3: dict(
                games_to_win=6, tb_at=6, best_of=3,
                tb_points_to_win=7, tb_win_by_two=True,
                deciding_set_mode=Match.DecidingSetMode.FULL_SET,
                deciding_tb_points_to_win=10,
            ),
            Match.Format.MANUAL: None,
        }

        if fmt in PRESETS and PRESETS[fmt]:
            for k, v in PRESETS[fmt].items():
                cleaned[k] = v

        return cleaned


class SelectEditionForm(forms.Form):
    edition = forms.ModelChoiceField(queryset=TournamentEdition.objects.order_by("-year"))


class SelectEventOnlyForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.none())

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop("edition")
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = (
            Event.objects.filter(edition=edition)
            .select_related("category")
            .order_by("category__name")
        )


class AddPlayerToEventForm(forms.Form):
    player = forms.ModelChoiceField(queryset=Player.objects.none())

    def __init__(self, *args, **kwargs):
        available_players = kwargs.pop("available_players")
        super().__init__(*args, **kwargs)
        self.fields["player"].queryset = available_players


# -----------------------
# Pages
# -----------------------

@superuser_required
def panel_home(request):
    return redirect("panel_select")


@superuser_required
def panel_select(request):
    # 1) Edition active par défaut
    active = TournamentEdition.objects.filter(is_active=True).order_by("-year").first()
    edition_id = request.GET.get("edition") or (str(active.id) if active else None)

    edition = None
    if edition_id:
        try:
            edition = TournamentEdition.objects.get(id=int(edition_id))
        except TournamentEdition.DoesNotExist:
            edition = None

    # Form édition (GET)
    edition_form = SelectEditionForm(initial={"edition": edition} if edition else None)

    # 2) Form event (POST)
    event_form = None
    if edition:
        event_form = SelectEventOnlyForm(request.POST or None, edition=edition)
        if request.method == "POST" and event_form.is_valid():
            event = event_form.cleaned_data["event"]
            return redirect("panel_event", event_id=event.id)

    return render(request, "live/panel_select.html", {
        "edition_form": edition_form,
        "event_form": event_form,
        "edition": edition,
    })


@superuser_required
def panel_event(request, event_id: int):
    return redirect("panel_players", event_id=event_id)


# -----------------------
# Actions : Players / Teams
# -----------------------

@superuser_required
def player_create(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)

    form = PlayerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        p = form.save()
        messages.success(request, f"Joueur créé: {p}")
        return redirect("panel_event", event_id=event.id)

    return render(request, "live/panel_player_form.html", {"event": event, "form": form, "mode": "create"})


def create_team_with_entry(event, player1, player2, name=""):
    """
    Service : crée un Team (double) puis l'inscrit dans l'event (Entry).
    `player1`/`player2` sont des instances Player distinctes.
    Refuse si l'event n'est pas en DOUBLE (ValueError).
    Retourne (team, entry).
    """
    if event.category.mode != Category.Mode.DOUBLE:
        raise ValueError("Cet event n'est pas en double.")
    if player1 == player2:
        raise ValueError("Les deux joueurs doivent être différents.")
    team = Team.objects.create(
        name=name or "",
        player1=player1,
        player2=player2,
    )
    entry, _ = Entry.objects.get_or_create(event=event, team=team)
    return team, entry


@superuser_required
def team_create(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("category"), id=event_id)
    if event.category.mode != Category.Mode.DOUBLE:
        messages.error(request, "Cet event n'est pas en double.")
        return redirect("panel_event", event_id=event.id)

    form = TeamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        t, _ = create_team_with_entry(
            event,
            form.cleaned_data["player1"],
            form.cleaned_data["player2"],
            form.cleaned_data["name"],
        )
        messages.success(request, f"Équipe créée + inscrite: {t}")
        return redirect("panel_event", event_id=event.id)

    return render(request, "live/panel_team_form.html", {"event": event, "form": form})


# -----------------------
# Actions : Poules
# -----------------------

def create_group(event, name):
    """
    Service : crée (ou récupère) une poule par son nom dans l'event.
    Retourne (group, created).
    """
    clean = (name or "").strip()
    if not clean:
        raise ValueError("Le nom de la poule est obligatoire.")
    return Group.objects.get_or_create(event=event, name=clean)


@superuser_required
def group_create(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)
    form = GroupCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_group(event, form.cleaned_data["name"])
        messages.success(request, "Poule créée.")
        return redirect("panel_event", event_id=event.id)
    return render(request, "live/panel_group_form.html", {"event": event, "form": form})


def autofill_groups(event, shuffle, group_size, num_groups=None):
    """
    Service : réinitialise les poules et répartit toutes les Entries de l'event
    en round-robin sur `num_groups` poules (A, B, C…). Réinitialise memberships
    et standings. Lève ValueError si l'épreuve est déjà débutée ou s'il n'y a
    aucune inscription. Retourne la liste des Group créés/utilisés.
    """
    _assert_groups_unlocked(event)
    entries = list(Entry.objects.filter(event=event))
    if not entries:
        raise ValueError("Aucune inscription (Entry) dans cet event.")

    if shuffle:
        random.shuffle(entries)

    group_size = int(group_size)
    if not num_groups:
        num_groups = max(1, (len(entries) + group_size - 1) // group_size)

    names = [chr(ord("A") + i) for i in range(int(num_groups))]
    groups = []
    for name in names:
        g, _ = Group.objects.get_or_create(event=event, name=name)
        groups.append(g)
        GroupMembership.objects.filter(group=g).delete()
        GroupStanding.objects.filter(group=g).delete()

    for idx, entry in enumerate(entries):
        g = groups[idx % len(groups)]
        GroupMembership.objects.create(group=g, entry=entry)

    return groups


@superuser_required
@transaction.atomic
def group_fill(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)
    form = GroupFillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            groups = autofill_groups(
                event,
                shuffle=form.cleaned_data["shuffle"],
                group_size=form.cleaned_data["group_size"],
                num_groups=form.cleaned_data.get("num_groups"),
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("panel_event", event_id=event.id)

        n_entries = Entry.objects.filter(event=event).count()
        messages.success(request, f"Poules remplies: {len(groups)} poules, {n_entries} participants.")
        return redirect("panel_event", event_id=event.id)

    return render(request, "live/panel_group_fill.html", {"event": event, "form": form})


# -----------------------
# Actions : Générer matchs de poule
# -----------------------

def generate_group_matches_for_event(event):
    """
    Service : génère le round-robin de chaque poule (≥2 entries) de l'event.
    Idempotent (ignore les paires déjà créées dans les deux sens). Format par
    défaut G_SET5_TB44, statut SCHEDULED. Retourne (created, matches).
    """
    groups = Group.objects.filter(event=event).prefetch_related("memberships__entry")

    created = 0
    matches = []
    for g in groups:
        entries = [m.entry for m in g.memberships.all()]
        if len(entries) < 2:
            continue

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                a = entries[i]
                b = entries[j]

                # éviter doublons (a,b) vs (b,a)
                exists = Match.objects.filter(
                    event=event,
                    group=g,
                    stage=Match.Stage.GROUP,
                    side_a=a, side_b=b
                ).exists() or Match.objects.filter(
                    event=event,
                    group=g,
                    stage=Match.Stage.GROUP,
                    side_a=b, side_b=a
                ).exists()

                if exists:
                    continue

                m = Match.objects.create(
                    event=event,
                    group=g,
                    stage=Match.Stage.GROUP,
                    side_a=a,
                    side_b=b,
                    match_format="G_SET5_TB44",
                    status=Match.Status.SCHEDULED,
                )
                matches.append(m)
                created += 1

    return created, matches


@superuser_required
@transaction.atomic
def generate_group_matches(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)
    created, _ = generate_group_matches_for_event(event)
    messages.success(request, f"Matchs de poule générés: {created} créés.")
    return redirect("panel_event", event_id=event.id)


# -----------------------
# Services : Cycle de vie de l'épreuve
# -----------------------

@transaction.atomic
def start_event(event):
    """
    Service : passe l'épreuve de INSCRIPTION → EN_COURS.
    - Génère le round-robin de chaque poule jouable (≥ 2 entries).
    - Crée le squelette du tableau final.
    - Met status = EN_COURS.
    Retourne {"created": int, "unplaced": [Entry, ...]}.
    Lève ValueError si le statut n'est pas INSCRIPTION ou si aucune poule jouable.
    """
    if event.status != Event.Status.INSCRIPTION:
        raise ValueError(f"Impossible de démarrer : statut actuel = {event.status}.")

    # poules jouables = au moins 2 entries
    playable_groups = [
        g for g in Group.objects.filter(event=event).prefetch_related("memberships")
        if g.memberships.count() >= 2
    ]
    if not playable_groups:
        raise ValueError("Aucune poule jouable (au moins 2 inscrits par poule requis).")

    # entries non affectées à une poule
    placed_entry_ids = set(
        GroupMembership.objects.filter(group__event=event).values_list("entry_id", flat=True)
    )
    all_entry_ids = set(Entry.objects.filter(event=event).values_list("id", flat=True))
    unplaced_ids = all_entry_ids - placed_entry_ids
    unplaced = list(Entry.objects.filter(id__in=unplaced_ids).select_related("player", "team"))

    created, _ = generate_group_matches_for_event(event)
    ensure_final_bracket_exists(event)

    event.status = Event.Status.EN_COURS
    event.save(update_fields=["status"])

    return {"created": created, "unplaced": unplaced}


@transaction.atomic
def close_event(event):
    """
    Service : passe l'épreuve EN_COURS → TERMINEE si la finale (F1) est FINISHED.
    Idempotent : no-op si déjà TERMINEE.
    Lève ValueError si la finale n'est pas terminée.
    """
    if event.status == Event.Status.TERMINEE:
        return
    if event.status != Event.Status.EN_COURS:
        raise ValueError(f"Impossible de clôturer : statut actuel = {event.status}.")

    finale = Match.objects.filter(
        event=event, stage=Match.Stage.F, bracket_slot="F1"
    ).first()
    if not finale or finale.status != Match.Status.FINISHED:
        raise ValueError("La finale (F1) n'est pas encore terminée.")

    event.status = Event.Status.TERMINEE
    event.save(update_fields=["status"])


@transaction.atomic
def reopen_event(event):
    """
    Service : passe l'épreuve TERMINEE → EN_COURS (recours admin).
    Lève ValueError si le statut n'est pas TERMINEE.
    """
    if event.status != Event.Status.TERMINEE:
        raise ValueError(f"Impossible de rouvrir : statut actuel = {event.status}.")

    event.status = Event.Status.EN_COURS
    event.save(update_fields=["status"])


# -----------------------
# Actions : Matches (edit + feature)
# -----------------------

def finalize_match_edit(match):
    """
    Service : logique post-sauvegarde commune à l'édition d'un match
    (sanitisation des valeurs négatives, cohérence du tie-break, retrait
    featured/file si terminé, puis synchronisation des gagnants du bracket).
    Le match est supposé déjà passé par MatchEditForm.save().
    Retourne le match.
    """
    for f in ["points_a", "points_b", "games_a", "games_b", "sets_a", "sets_b", "tb_points_a", "tb_points_b"]:
        val = getattr(match, f, 0)
        if val is None or val < 0:
            setattr(match, f, 0)

    if not match.tb_active:
        match.tb_points_a = 0
        match.tb_points_b = 0

    if match.status == Match.Status.FINISHED:
        match.is_featured = False

    if match.status == Match.Status.CANCELED:
        match.order_index = None
        match.scheduled_time = None
        match.is_featured = False

    match.save()

    if match.status == Match.Status.FINISHED and match.stage in (Match.Stage.QF, Match.Stage.SF):
        from live.bracket import sync_final_winners_for_event
        sync_final_winners_for_event(match.event)

    if match.status == Match.Status.FINISHED and match.stage == Match.Stage.F:
        try:
            close_event(match.event)
        except ValueError:
            pass

    return match


@superuser_required
def match_edit(request, event_id: int, match_id: int):
    event = get_object_or_404(Event, id=event_id)
    match = get_object_or_404(Match, id=match_id, event=event)

    form = MatchEditForm(request.POST or None, instance=match)

    if request.method == "POST" and form.is_valid():
        form.save()
        finalize_match_edit(form.instance)
        messages.success(request, "Match mis à jour.")
        return redirect("panel_matches", event_id=event.id)

    return render(request, "live/panel_match_form.html", {"event": event, "match": match, "form": form})


def feature_match(match):
    """
    Service : met un match « en avant » et le démarre. Retire le drapeau des
    autres matchs de l'event, met is_featured=True, puis
    mark_live() (status=LIVE + started_at). Source : match_feature.
    Retourne le match.
    """
    Match.objects.filter(event=match.event, is_featured=True).update(is_featured=False)
    match.is_featured = True
    match.mark_live()  # met status=LIVE + started_at si besoin
    match.save()
    return match


@superuser_required
@transaction.atomic
def match_feature(request, event_id: int, match_id: int):
    event = get_object_or_404(Event, id=event_id)
    match = get_object_or_404(Match, id=match_id, event=event)
    feature_match(match)
    messages.success(request, f"Match en cours: {match}")
    return redirect("panel_matches", event_id=event.id)


def add_player_entry(event, player):
    """
    Service : inscrit un Player (simple) dans l'event via une Entry.
    Refuse si l'event n'est pas en SINGLE (ValueError).
    Retourne l'Entry (créée ou déjà existante).
    """
    if event.category.mode != Category.Mode.SINGLE:
        raise ValueError("Ajout joueur direct : uniquement pour un event en simple.")
    entry, _ = Entry.objects.get_or_create(event=event, player=player)
    return entry


def add_players_entries(event, player_ids):
    """
    Service : inscrit plusieurs Players (simple) dans l'event.
    Refuse si l'event n'est pas en SINGLE (ValueError).
    Ignore les joueurs déjà inscrits ou inconnus.
    Retourne (created_entries, skipped_player_ids).
    """
    if event.category.mode != Category.Mode.SINGLE:
        raise ValueError("Ajout de joueurs : uniquement pour un event en simple.")

    existing_player_ids = set(
        Entry.objects.filter(event=event, player__isnull=False).values_list("player_id", flat=True)
    )
    to_add_ids = [pid for pid in player_ids if pid not in existing_player_ids]

    players_by_id = {p.id: p for p in Player.objects.filter(id__in=to_add_ids)}

    created = []
    for pid in player_ids:
        player = players_by_id.get(pid)
        if player is None:
            continue
        entry, was_created = Entry.objects.get_or_create(event=event, player=player)
        if was_created:
            created.append(entry)

    created_ids = {e.player_id for e in created}
    skipped = [pid for pid in player_ids if pid not in created_ids]
    return created, skipped


def remove_entry(event, entry):
    """
    Service : retire une Entry de l'event.
    Refuse (ValueError) si l'Entry est déjà engagée dans un match.
    """
    used_in_matches = Match.objects.filter(event=event, side_a=entry).exists() or \
        Match.objects.filter(event=event, side_b=entry).exists()
    if used_in_matches:
        raise ValueError(
            f"Impossible de retirer {entry} : déjà utilisé dans un ou plusieurs matchs."
        )
    entry.delete()


@transaction.atomic
def withdraw_entry(entry):
    """
    Service : déclare le forfait d'une Entry (EN_COURS requis).
    - Pose entry.withdrawn = True.
    - Tous les matchs non terminés (SCHEDULED/LIVE) → FINISHED, is_walkover=True,
      winner_side = adversaire, score de convention (games_to_win / 0).
    - Recalcule les standings de chaque poule affectée.
    - Propage les vainqueurs du tableau (QF/SF/F).
    Lève ValueError si l'event n'est pas EN_COURS.
    Retourne {"matches_walkover": int}.
    """
    from competition.standings import recalc_one_group

    event = entry.event
    if event.status != Event.Status.EN_COURS:
        raise ValueError(f"Impossible de déclarer un forfait : statut = {event.status}.")

    entry.withdrawn = True
    entry.save(update_fields=["withdrawn"])

    non_finished = Match.objects.filter(
        event=event,
        status__in=[Match.Status.SCHEDULED, Match.Status.LIVE],
    ).filter(
        Q(side_a=entry) | Q(side_b=entry)
    )

    affected_groups = set()
    has_qf_sf = False
    has_finale = False
    count = 0

    for m in non_finished:
        if m.side_a_id == entry.id:
            m.winner_side = Match.WinnerSide.B
            m.games_a = 0
            m.games_b = m.games_to_win
        else:
            m.winner_side = Match.WinnerSide.A
            m.games_a = m.games_to_win
            m.games_b = 0

        m.status = Match.Status.FINISHED
        m.is_walkover = True
        m.is_featured = False
        if not m.finished_at:
            m.finished_at = timezone.now()

        m.save(update_fields=[
            "winner_side", "games_a", "games_b",
            "status", "is_walkover", "is_featured", "finished_at",
        ])

        if m.group_id:
            affected_groups.add(m.group_id)
        if m.stage in (Match.Stage.QF, Match.Stage.SF):
            has_qf_sf = True
        if m.stage == Match.Stage.F:
            has_finale = True
        count += 1

    for gid in affected_groups:
        recalc_one_group(gid)

    if affected_groups:
        from live.bracket import sync_final_bracket_for_event
        sync_final_bracket_for_event(event)

    if has_qf_sf:
        from live.bracket import sync_final_winners_for_event
        sync_final_winners_for_event(event)

    if has_finale:
        try:
            close_event(event)
        except ValueError:
            pass

    return {"matches_walkover": count}


@transaction.atomic
def add_late_entry(event, group, player=None, team=None):
    """
    Service : ajout tardif d'un inscrit dans une poule, en EN_COURS.
    - Crée l'Entry (player ou team) si elle n'existe pas déjà.
    - Crée le GroupMembership dans la poule désignée.
    - Ré-exécute generate_group_matches_for_event (additif) → seuls les matchs
      du nouveau venu sont créés ; les matchs déjà joués ne bougent pas.
    Lève ValueError si event.status != EN_COURS, si player et team sont tous
    les deux None, ou si le player/team est déjà inscrit dans l'event.
    Retourne (entry, created_count, over_capacity).
    """
    if event.status != Event.Status.EN_COURS:
        raise ValueError(f"Impossible d'ajouter un inscrit tardif : statut = {event.status}.")

    if player is None and team is None:
        raise ValueError("Il faut renseigner un joueur (simple) ou une équipe (double).")

    if player is not None and Entry.objects.filter(event=event, player=player).exists():
        raise ValueError(f"{player} est déjà inscrit dans cette épreuve.")
    if team is not None and Entry.objects.filter(event=event, team=team).exists():
        raise ValueError(f"{team} est déjà inscrit dans cette épreuve.")

    entry = Entry.objects.create(event=event, player=player, team=team)
    GroupMembership.objects.get_or_create(group=group, entry=entry)

    current_size = GroupMembership.objects.filter(group=group).count()
    over_capacity = current_size > event.group_size_default

    created_count, _ = generate_group_matches_for_event(event)

    return entry, created_count, over_capacity


@transaction.atomic
def replace_entry_player(entry, player=None, team=None):
    """
    Service : remplace le player/team d'une Entry existante.
    La place en poule et les résultats déjà joués sont conservés ; aucun match recréé.
    Lève ValueError si player et team sont tous les deux None, si la catégorie ne
    correspond pas (SINGLE/DOUBLE), ou si le nouveau player/team est déjà inscrit
    dans le même event.
    Retourne l'Entry mise à jour.
    """
    if player is None and team is None:
        raise ValueError("Il faut renseigner un joueur (simple) ou une équipe (double).")

    mode = entry.event.category.mode
    if mode == Category.Mode.SINGLE and player is None:
        raise ValueError("Cette catégorie est en simple : il faut un joueur.")
    if mode == Category.Mode.DOUBLE and team is None:
        raise ValueError("Cette catégorie est en double : il faut une équipe.")

    if player is not None and Entry.objects.filter(event=entry.event, player=player).exclude(pk=entry.pk).exists():
        raise ValueError(f"{player} est déjà inscrit dans cette épreuve.")
    if team is not None and Entry.objects.filter(event=entry.event, team=team).exclude(pk=entry.pk).exists():
        raise ValueError(f"{team} est déjà inscrit dans cette épreuve.")

    entry.player = player
    entry.team = team
    entry.save(update_fields=["player", "team"])
    return entry


@superuser_required
def entry_add_player(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("category"), id=event_id)

    # Seulement pour les events "simple"
    if event.category.mode != Category.Mode.SINGLE:
        messages.error(request, "Ajout joueur direct : uniquement pour un event en simple.")
        return redirect("panel_event", event_id=event.id)

    existing_player_ids = Entry.objects.filter(event=event, player__isnull=False).values_list("player_id", flat=True)
    available_players = Player.objects.exclude(id__in=existing_player_ids).order_by("last_name", "first_name")

    form = AddPlayerToEventForm(request.POST or None, available_players=available_players)
    if request.method == "POST" and form.is_valid():
        p = form.cleaned_data["player"]
        add_player_entry(event, p)
        messages.success(request, f"Joueur inscrit à l'event : {p}")
        return redirect("panel_event", event_id=event.id)

    # si aucun joueur dispo
    if not available_players.exists():
        messages.info(request, "Tous les joueurs sont déjà inscrits à cet event.")
        return redirect("panel_event", event_id=event.id)

    return render(request, "live/panel_add_player.html", {"event": event, "form": form})


@superuser_required
@require_POST
def entry_add_players(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("category"), id=event_id)

    # uniquement pour SIMPLE
    if event.category.mode != Category.Mode.SINGLE:
        messages.error(request, "Ajout de joueurs : uniquement pour un event en simple.")
        return redirect("panel_event", event_id=event.id)

    # players sélectionnés (multiple)
    ids = request.POST.getlist("player_ids")
    if not ids:
        messages.warning(request, "Aucun joueur sélectionné.")
        return redirect("panel_event", event_id=event.id)

    # sécurité : ne prendre que des IDs valides d'entiers
    try:
        ids = [int(x) for x in ids]
    except ValueError:
        messages.error(request, "Sélection invalide.")
        return redirect("panel_event", event_id=event.id)

    created, _ = add_players_entries(event, ids)
    if not created:
        messages.info(request, "Tous les joueurs sélectionnés étaient déjà inscrits.")
        return redirect("panel_event", event_id=event.id)

    messages.success(request, f"{len(created)} joueur(s) ajouté(s) à l'event.")
    return redirect("panel_event", event_id=event.id)


@superuser_required
@require_POST
def entry_remove(request, event_id: int, entry_id: int):
    event = get_object_or_404(Event, id=event_id)
    entry = get_object_or_404(Entry, id=entry_id, event=event)

    label = str(entry)

    # Sécurité : si déjà utilisé dans des matchs, on empêche (optionnel mais recommandé)
    try:
        remove_entry(event, entry)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("panel_event", event_id=event.id)

    messages.success(request, f"{label} retiré de l’event.")
    return redirect("panel_event", event_id=event.id)


@superuser_required
def panel_players(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("edition", "category"), id=event_id)

    entries = Entry.objects.filter(event=event).select_related("player", "team")
    players = Player.objects.order_by("last_name", "first_name")

    existing_player_ids = Entry.objects.filter(event=event, player__isnull=False).values_list("player_id", flat=True)
    available_players = Player.objects.exclude(id__in=existing_player_ids).order_by("last_name", "first_name")

    return render(request, "live/panel_players.html", {
        "event": event,
        "entries": entries,
        "players": players,
        "available_players": available_players,
        "tab": "players",
        **panel_counts(event),
    })


@superuser_required
def panel_groups(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("edition", "category"), id=event_id)

    groups = Group.objects.filter(event=event).order_by("name").prefetch_related("memberships__entry")
    entries = list(Entry.objects.filter(event=event).select_related("player", "team"))

    assigned_ids = set(
        GroupMembership.objects.filter(group__event=event).values_list("entry_id", flat=True)
    )
    unassigned = [e for e in entries if e.id not in assigned_ids]

    return render(request, "live/panel_groups.html", {
        "event": event,
        "groups": groups,
        "unassigned": unassigned,
        "tab": "groups",
        **panel_counts(event),
    })


@superuser_required
def panel_matches(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("edition", "category"), id=event_id)

    current_match = (
        Match.objects.filter(edition=event.edition, status=Match.Status.LIVE)
        .select_related("event", "side_a", "side_b", "court", "group")
        .order_by("-updated_at", "-id")
        .first()
    )

    # # 2) Fallback: si aucun LIVE, on prend éventuellement le "featured"
    # if current_match is None:
    #     current_match = (
    #         Match.objects.filter(event=event, is_featured=True)
    #         .select_related("side_a", "side_b", "court", "group")
    #         .order_by("-updated_at", "-id")
    #         .first()
    #     )

    finished = list(
        Match.objects.filter(event=event, status=Match.Status.FINISHED)
        .select_related("side_a", "side_b", "court", "group")
        .order_by("-updated_at", "-id")
    )

    # Matchs "planifiés/en cours" ordonnés
    queue = list(
        Match.objects.filter(
            event=event,
            status__in=[Match.Status.SCHEDULED, Match.Status.LIVE],
            order_index__isnull=False,
        )
        .exclude(id=current_match.id if current_match else None)
        .select_related("side_a", "side_b", "court", "group")
        .order_by("order_index")
    )

    # Matchs "planifiés/en cours" non ordonnés
    backlog = list(
        Match.objects.filter(
            event=event,
            status__in=[Match.Status.SCHEDULED, Match.Status.LIVE],
            order_index__isnull=True,
        )
        .exclude(id=current_match.id if current_match else None)
        .select_related("side_a", "side_b", "court", "group")
        .order_by("stage", "group__name", "id")
    )

    return render(request, "live/panel_matches.html", {
        "event": event,
        "current_match": current_match,
        "queue": queue,
        "backlog": backlog,
        "finished": finished,
        "tab": "matches",
        **panel_counts(event),
    })


def _final_matches_qs(event):
    return Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
    )


def assign_bracket_entry(event, match_id: int, entry_id: int, side: str):
    """
    Assigne une Entry (entry_id) à un côté (side='A'|'B') d'un match de tableau final.
    Déplace automatiquement l'Entry si elle est déjà dans un autre slot planifié.
    Lève ValueError pour tout état invalide.
    """
    side = side.upper()
    if side not in {"A", "B"}:
        raise ValueError("side doit valoir 'A' ou 'B'.")

    match = get_object_or_404(
        Match,
        id=match_id,
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
    )
    entry = get_object_or_404(Entry, id=entry_id, event=event)

    if match.status != Match.Status.SCHEDULED:
        raise ValueError("Match déjà lancé.")

    other_side = match.side_b if side == "A" else match.side_a
    if other_side and other_side.id == entry.id:
        raise ValueError("Un participant ne peut pas être des deux côtés.")

    # Retirer l'entrée de tout autre slot planifié du tableau final.
    _final_matches_qs(event).filter(status=Match.Status.SCHEDULED, side_a=entry).update(side_a=None)
    _final_matches_qs(event).filter(status=Match.Status.SCHEDULED, side_b=entry).update(side_b=None)

    if side == "A":
        match.side_a = entry
        match.save(update_fields=["side_a"])
    else:
        match.side_b = entry
        match.save(update_fields=["side_b"])


def clear_bracket_entry(event, match_id: int, side: str):
    """
    Retire l'Entry du côté (side='A'|'B') d'un match de tableau final planifié.
    Lève ValueError pour tout état invalide.
    """
    side = side.upper()
    if side not in {"A", "B"}:
        raise ValueError("side doit valoir 'A' ou 'B'.")

    match = get_object_or_404(
        Match,
        id=match_id,
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
    )

    if match.status != Match.Status.SCHEDULED:
        raise ValueError("Match déjà lancé.")

    if side == "A":
        match.side_a = None
        match.save(update_fields=["side_a"])
    else:
        match.side_b = None
        match.save(update_fields=["side_b"])


def _create_final_bracket(event, start_stage: str) -> int:
    """
    Crée un tableau final manuel à partir d'une étape (QF, SF ou F).
    Retourne le nombre de matchs créés.
    """
    created = 0

    def create_match(stage, slot, fmt, a_label=None, b_label=None):
        nonlocal created
        rules = {
            Match.Format.GROUP_SET5_TB_4_4: dict(games_to_win=5, tb_at=4, best_of=1),
            Match.Format.QF_SET5_TB_5_5: dict(games_to_win=6, tb_at=5, best_of=1),
            Match.Format.NORMAL_1SET: dict(games_to_win=6, tb_at=6, best_of=1),
            Match.Format.BO3: dict(games_to_win=6, tb_at=6, best_of=3),
        }.get(fmt, dict(games_to_win=5, tb_at=4, best_of=1))

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
        created += 1

    if start_stage == Match.Stage.QF:
        create_match(Match.Stage.QF, "QF1", Match.Format.QF_SET5_TB_5_5)
        create_match(Match.Stage.QF, "QF2", Match.Format.QF_SET5_TB_5_5)
        create_match(Match.Stage.QF, "QF3", Match.Format.QF_SET5_TB_5_5)
        create_match(Match.Stage.QF, "QF4", Match.Format.QF_SET5_TB_5_5)
        create_match(Match.Stage.SF, "SF1", Match.Format.NORMAL_1SET, "WQF1", "WQF2")
        create_match(Match.Stage.SF, "SF2", Match.Format.NORMAL_1SET, "WQF3", "WQF4")
        create_match(Match.Stage.F, "F1", Match.Format.BO3, "WSF1", "WSF2")
    elif start_stage == Match.Stage.SF:
        create_match(Match.Stage.SF, "SF1", Match.Format.NORMAL_1SET)
        create_match(Match.Stage.SF, "SF2", Match.Format.NORMAL_1SET)
        create_match(Match.Stage.F, "F1", Match.Format.BO3, "WSF1", "WSF2")
    elif start_stage == Match.Stage.F:
        create_match(Match.Stage.F, "F1", Match.Format.BO3)

    return created


def create_final_bracket_for_event(event, start_stage, force=False):
    """
    Service réutilisable : crée (ou recrée) le tableau final manuel à partir
    d'une étape de départ (QF/SF/F). Lève ``ValueError`` (message FR) si l'étape
    est invalide, si un tableau existe déjà sans ``force``, ou si une recréation
    est demandée alors qu'un match est déjà lancé/terminé.
    Retourne le nombre de matchs créés.
    """
    start_stage = (start_stage or "").upper().strip()
    if start_stage not in {Match.Stage.QF, Match.Stage.SF, Match.Stage.F}:
        raise ValueError("Étape de départ invalide.")

    existing = _final_matches_qs(event)
    if existing.exists():
        if not force:
            raise ValueError("Un tableau final existe déjà. Utilise 'Recréer' si besoin.")
        if existing.exclude(status=Match.Status.SCHEDULED).exists():
            raise ValueError("Impossible de recréer : un match est déjà en cours ou terminé.")
        existing.delete()

    return _create_final_bracket(event, start_stage)


def set_match_bracket_labels(match, a_label, b_label):
    """
    Service réutilisable : met à jour les labels (A1, D2, WSF1…) d'un match du
    tableau final. Lève ``ValueError`` si le match n'est plus ``SCHEDULED``.
    """
    if match.status != Match.Status.SCHEDULED:
        raise ValueError("Impossible de modifier les labels : match déjà lancé.")
    match.side_a_label = (a_label or "").strip().upper() or None
    match.side_b_label = (b_label or "").strip().upper() or None
    match.save(update_fields=["side_a_label", "side_b_label"])
    return match


@superuser_required
def panel_final(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("edition", "category"), id=event_id)

    finals = _final_matches_qs(event).select_related("side_a", "side_b").order_by("stage", "bracket_slot")
    has_bracket = finals.exists()

    qf = list(finals.filter(stage=Match.Stage.QF).order_by("bracket_slot"))
    sf = list(finals.filter(stage=Match.Stage.SF).order_by("bracket_slot"))
    f1 = finals.filter(stage=Match.Stage.F, bracket_slot="F1").first()

    entries = list(Entry.objects.filter(event=event).select_related("player", "team"))
    assigned_ids = set(finals.values_list("side_a_id", flat=True)) | set(finals.values_list("side_b_id", flat=True))

    event_group_tables = build_event_group_tables(event.edition, [event])
    group_tables = event_group_tables.get(event.id, [])

    return render(request, "live/panel_final.html", {
        "event": event,
        "qf": qf,
        "sf": sf,
        "final": f1,
        "has_bracket": has_bracket,
        "entries": entries,
        "assigned_ids": assigned_ids,
        "group_tables": group_tables,
        "tab": "final",
        **panel_counts(event),
    })


@superuser_required
@require_POST
def panel_final_create(request, event_id: int):
    event = get_object_or_404(Event.objects.select_related("edition"), id=event_id)
    force = request.POST.get("force") == "1"

    try:
        created = create_final_bracket_for_event(event, request.POST.get("start_stage"), force)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("panel_final", event_id=event.id)

    messages.success(request, f"Tableau final créé ({created} matchs).")
    return redirect("panel_final", event_id=event.id)


@superuser_required
@require_POST
def panel_final_label_update(request, event_id: int, match_id: int):
    event = get_object_or_404(Event, id=event_id)
    match = get_object_or_404(Match, id=match_id, event=event, stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F])

    try:
        set_match_bracket_labels(match, request.POST.get("side_a_label"), request.POST.get("side_b_label"))
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("panel_final", event_id=event.id)

    messages.success(request, "Labels mis à jour.")
    return redirect("panel_final", event_id=event.id)


@superuser_required
@require_POST
def panel_final_clear(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)

    if request.content_type and request.content_type.startswith("application/json"):
        try:
            payload = json.loads(request.body or b"{}")
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "error": "Corps JSON invalide."}, status=400)
    else:
        payload = request.POST

    match_id = payload.get("match_id")
    side = (payload.get("side") or "").upper()

    if not match_id or side not in {"A", "B"}:
        return JsonResponse({"ok": False, "error": "Paramètres manquants."}, status=400)

    try:
        clear_bracket_entry(event, int(match_id), side)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


@superuser_required
@require_POST
def panel_final_assign(request, event_id: int):
    event = get_object_or_404(Event, id=event_id)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except ValueError:
        payload = {}

    match_id = payload.get("match_id")
    entry_id = payload.get("entry_id")
    side = (payload.get("side") or "").upper()

    if not match_id or not entry_id or side not in {"A", "B"}:
        return JsonResponse({"ok": False, "error": "Paramètres manquants."}, status=400)

    try:
        assign_bracket_entry(event, int(match_id), int(entry_id), side)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True})


@superuser_required
def player_edit(request, event_id: int, player_id: int):
    event = get_object_or_404(Event, id=event_id)
    player = get_object_or_404(Player, id=player_id)

    form = PlayerForm(request.POST or None, instance=player)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Joueur modifié.")
        return redirect("panel_players", event_id=event.id)

    return render(request, "live/panel_player_form.html", {
        "event": event,
        "form": form,
        "mode": "edit",
        "player": player,
    })


def _assert_groups_unlocked(event):
    """Lève ValueError si l'épreuve n'est plus en phase d'inscription (poules verrouillées)."""
    if event.status != Event.Status.INSCRIPTION:
        raise ValueError("Épreuve déjà débutée : composition des poules verrouillée.")


def assign_entry_to_group(event, entry, group):
    """
    Service : assigne (ou déplace) une Entry dans une poule. Retire d'abord
    l'entry de toute autre poule de l'event. Lève ValueError si les poules sont
    verrouillées (status != INSCRIPTION).
    """
    _assert_groups_unlocked(event)
    GroupMembership.objects.filter(entry=entry, group__event=event).delete()
    GroupMembership.objects.get_or_create(group=group, entry=entry)


def unassign_entry(event, entry):
    """
    Service : retire une Entry de sa poule (retour en 'Non affectés').
    Lève ValueError si les poules sont verrouillées.
    """
    _assert_groups_unlocked(event)
    GroupMembership.objects.filter(entry=entry, group__event=event).delete()


@superuser_required
@require_POST
@transaction.atomic
def group_assign(request, event_id: int):
    """
    Assigne (ou déplace) une Entry dans une poule.
    POST: entry_id, group_id
    """
    event = get_object_or_404(Event, id=event_id)
    entry_id = request.POST.get("entry_id")
    group_id = request.POST.get("group_id")

    if not entry_id or not group_id:
        return JsonResponse({"ok": False, "error": "Paramètres manquants"}, status=400)

    entry = get_object_or_404(Entry, id=int(entry_id), event=event)
    group = get_object_or_404(Group, id=int(group_id), event=event)

    try:
        assign_entry_to_group(event, entry, group)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True})


@superuser_required
@require_POST
@transaction.atomic
def group_unassign(request, event_id: int):
    """
    Retire une Entry de sa poule (la remet en 'Non affectés').
    POST: entry_id
    """
    event = get_object_or_404(Event, id=event_id)
    entry_id = request.POST.get("entry_id")

    if not entry_id:
        return JsonResponse({"ok": False, "error": "Paramètres manquants"}, status=400)

    entry = get_object_or_404(Entry, id=int(entry_id), event=event)

    try:
        unassign_entry(event, entry)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True})


def _pick(group, rank):
    return group.standings.select_related("entry").get(rank=rank).entry


# def build_final_bracket_for_event(event):
#     groups = list(Group.objects.filter(event=event).order_by("name"))
#     group_names = [g.name.upper() for g in groups]

#     if event.qualified_per_group != 2:
#         raise ValueError("Cette génération suppose qualified_per_group=2 (A1/A2...).")

#     # Vérifie que toutes les poules sont prêtes
#     for g in groups:
#         if not g.ready_for_qualification():
#             raise ValueError(f"Poule {g.name} pas prête (matchs pas finis ou ranks manquants).")

#     # Map A/B/C/D
#     by_name = {g.name.upper(): g for g in groups}

#     with transaction.atomic():
#         # On supprime l'ancien tableau final de l'event (QF/SF/F)
#         Match.objects.filter(event=event, stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F]).delete()

#         if len(groups) == 4:
#             A, B, C, D = by_name["A"], by_name["B"], by_name["C"], by_name["D"]
#             A1, A2 = _pick(A, 1), _pick(A, 2)
#             B1, B2 = _pick(B, 1), _pick(B, 2)
#             C1, C2 = _pick(C, 1), _pick(C, 2)
#             D1, D2 = _pick(D, 1), _pick(D, 2)

#             pairings = [
#                 ("QF1", A1, D2),
#                 ("QF2", C1, B2),
#                 ("QF3", B1, C2),
#                 ("QF4", D1, A2),
#             ]

#             for slot, ea, eb in pairings:
#                 Match.objects.create(
#                     edition=event.edition,
#                     event=event,
#                     stage=Match.Stage.QF,
#                     bracket_slot=slot,
#                     match_format=Match.Format.QF_SET5_TB_5_5,
#                     side_a=ea,
#                     side_b=eb,
#                     status=Match.Status.SCHEDULED,
#                 )

#             # on peut créer les SF/F "vides" plus tard quand on sait les gagnants

#         elif len(groups) == 2:
#             A, B = by_name["A"], by_name["B"]
#             A1, A2 = _pick(A, 1), _pick(A, 2)
#             B1, B2 = _pick(B, 1), _pick(B, 2)

#             pairings = [
#                 ("SF1", A1, B2),
#                 ("SF2", B1, A2),
#             ]

#             for slot, ea, eb in pairings:
#                 Match.objects.create(
#                     edition=event.edition,
#                     event=event,
#                     stage=Match.Stage.SF,
#                     bracket_slot=slot,
#                     match_format=Match.Format.NORMAL_1SET,  # adapte si tu veux
#                     side_a=ea,
#                     side_b=eb,
#                     status=Match.Status.SCHEDULED,
#                 )

#         elif len(groups) == 1:
#             # pas de bracket (ou finale directe) -> on ne fait rien pour l'instant
#             return

#         else:
#             # 3 poules : règle à définir
#             raise ValueError("3 poules : règle de tableau final non définie pour l’instant.")


def _resolve_label_to_entry(event, label: str):
    """
    label ex: "A1" => poule A, rank 1
    Retourne Entry ou None
    """
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
    Crée le squelette du tableau final (QF ou SF) avec bracket_slot + labels (A1, D2...).
    Ne remplit pas forcément side_a/side_b.
    - 4 poules => QF1..QF4 (A1-D2, C1-B2, B1-C2, D1-A2)
    - 2 poules => SF1..SF2 (A1-B2, B1-A2)
    - 1 poule => rien
    - 3 poules => rien (règle non définie pour l’instant)
    """
    groups = list(Group.objects.filter(event=event).order_by("name"))
    n = len(groups)

    if event.qualified_per_group != 2:
        return  # on gère plus tard d'autres cas

    by_name = {g.name.upper(): g for g in groups}

    # helper create if missing
    def get_or_create(stage, slot, a_label, b_label, fmt):
        m = Match.objects.filter(event=event, stage=stage, bracket_slot=slot).first()
        if m:
            # met à jour les labels si besoin (sans toucher si match live/finished)
            if m.status == Match.Status.SCHEDULED:
                m.side_a_label = a_label
                m.side_b_label = b_label
                m.match_format = fmt
                m.save()
            return m

        return Match.objects.create(
            edition=event.edition,
            event=event,
            stage=stage,
            bracket_slot=slot,
            match_format=fmt,
            status=Match.Status.SCHEDULED,
            side_a=None,
            side_b=None,
            side_a_label=a_label,
            side_b_label=b_label,
        )

    if n == 4 and all(k in by_name for k in ["A", "B", "C", "D"]):
        get_or_create(Match.Stage.QF, "QF1", "A1", "D2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF2", "C1", "B2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF3", "B1", "C2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.QF, "QF4", "D1", "A2", Match.Format.QF_SET5_TB_5_5)
        get_or_create(Match.Stage.SF, "SF1", "WQF1", "WQF2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.SF, "SF2", "WQF3", "WQF4", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.F, "F1", "WSF1", "WSF2", Match.Format.BO3)

    elif n == 2 and all(k in by_name for k in ["A", "B"]):
        get_or_create(Match.Stage.SF, "SF1", "A1", "B2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.SF, "SF2", "B1", "A2", Match.Format.NORMAL_1SET)
        get_or_create(Match.Stage.F, "F1", "WSF1", "WSF2", Match.Format.BO3)

    else:
        # 1 poule => rien ; 3 poules => non géré
        return


def sync_final_bracket_for_event(event):
    """
    Remplit side_a/side_b des matchs de tableau final dès que les ranks existent.
    Ne modifie que les matchs SCHEDULED.
    """
    ensure_final_bracket_exists(event)

    qs = Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F],
        status=Match.Status.SCHEDULED,
    )

    for m in qs:
        changed = False

        if m.side_a_id is None and m.side_a_label:
            ea = _resolve_label_to_entry(event, m.side_a_label)
            if ea:
                m.side_a = ea
                changed = True

        if m.side_b_id is None and m.side_b_label:
            eb = _resolve_label_to_entry(event, m.side_b_label)
            if eb:
                m.side_b = eb
                changed = True

        if changed:
            m.save()


# =========================================================================
# Phase 9 — Administration de la configuration (services réutilisables)
# Éditions, catégories, courts, épreuves. CRUD neuf : aucune logique
# existante à extraire d'une vue template, mais on garde le pattern
# « service réutilisable » exposé par-dessus en endpoint /api/ JSON fin.
# Toutes les validations métier vivent ici ; les vues lèvent juste 400.
# =========================================================================

_NOCHANGE = object()  # sentinelle « champ non fourni » pour les éditions partielles


def _as_choice_int(value, allowed, label):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} : valeur invalide.")
    if v not in allowed:
        raise ValueError(f"{label} doit valoir {' ou '.join(str(a) for a in allowed)}.")
    return v


def _parse_year(value):
    try:
        year = int(value)
    except (TypeError, ValueError):
        raise ValueError("Année invalide.")
    if not (1900 <= year <= 3000):
        raise ValueError("Année hors plage (1900–3000).")
    return year


# ── Éditions ─────────────────────────────────────────────────────────────

def create_edition(name, year, start_dt=None, end_dt=None, activate=False):
    """Crée une édition. `year` unique. start/end_dt = datetime|None déjà parsés."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom de l'édition est requis.")
    year = _parse_year(year)
    if TournamentEdition.objects.filter(year=year).exists():
        raise ValueError(f"Une édition existe déjà pour l'année {year}.")
    edition = TournamentEdition(
        name=name,
        year=year,
        start_dt=start_dt or None,
        end_dt=end_dt or None,
        is_active=bool(activate),
    )
    edition.save()  # save() force l'exclusivité de is_active
    return edition


def update_edition(edition, name=_NOCHANGE, year=_NOCHANGE, start_dt=_NOCHANGE, end_dt=_NOCHANGE, **kwargs):
    """Édition partielle : seuls les champs fournis (≠ _NOCHANGE) sont touchés."""
    if name is not _NOCHANGE:
        name = (name or "").strip()
        if not name:
            raise ValueError("Le nom de l'édition est requis.")
        edition.name = name
    if year is not _NOCHANGE:
        y = _parse_year(year)
        if TournamentEdition.objects.filter(year=y).exclude(pk=edition.pk).exists():
            raise ValueError(f"Une édition existe déjà pour l'année {y}.")
        edition.year = y
    if start_dt is not _NOCHANGE:
        edition.start_dt = start_dt or None
    if end_dt is not _NOCHANGE:
        edition.end_dt = end_dt or None
    if "default_match_duration_min" in kwargs:
        edition.default_match_duration_min = kwargs["default_match_duration_min"]
    edition.save()
    return edition


def set_active_edition(edition):
    """Rend une édition courante. save() désactive automatiquement les autres."""
    edition.is_active = True
    edition.save()
    return edition


def delete_edition(edition):
    """Supprime une édition vide. Refusé si elle contient des épreuves (CASCADE destructif)."""
    if Event.objects.filter(edition=edition).exists():
        raise ValueError(
            "Impossible de supprimer une édition contenant des épreuves. "
            "Désactive-la plutôt (archive)."
        )
    edition.delete()


# ── Catégories ─────────────────────────────────────────────────────────────

def create_category(name, mode):
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom de la catégorie est requis.")
    if mode not in Category.Mode.values:
        raise ValueError("Mode invalide (attendu « S » ou « D »).")
    if Category.objects.filter(name__iexact=name).exists():
        raise ValueError(f"Une catégorie nommée « {name} » existe déjà.")
    return Category.objects.create(name=name, mode=mode)


def update_category(category, name=_NOCHANGE, mode=_NOCHANGE):
    if name is not _NOCHANGE:
        name = (name or "").strip()
        if not name:
            raise ValueError("Le nom de la catégorie est requis.")
        if Category.objects.filter(name__iexact=name).exclude(pk=category.pk).exists():
            raise ValueError(f"Une catégorie nommée « {name} » existe déjà.")
        category.name = name
    if mode is not _NOCHANGE and mode != category.mode:
        if mode not in Category.Mode.values:
            raise ValueError("Mode invalide (attendu « S » ou « D »).")
        # Le mode pilote Entry.clean() (joueur XOR équipe) : on bloque le
        # changement dès qu'une inscription existe sur une épreuve de la catégorie.
        if Entry.objects.filter(event__category=category).exists():
            raise ValueError(
                "Impossible de changer le mode : des inscriptions existent "
                "sur des épreuves de cette catégorie."
            )
        category.mode = mode
    category.save()
    return category


def delete_category(category):
    """Refusé si ≥1 épreuve l'utilise (FK PROTECT → on vérifie avant pour lever un 400 propre)."""
    events = list(Event.objects.filter(category=category).select_related("edition"))
    if events:
        years = ", ".join(sorted({str(e.edition.year) for e in events}))
        raise ValueError(f"Catégorie utilisée par des épreuves ({years}). Supprime-les d'abord.")
    category.delete()


# ── Courts ───────────────────────────────────────────────────────────────

def create_court(name):
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom du court est requis.")
    if Court.objects.filter(name__iexact=name).exists():
        raise ValueError(f"Un court nommé « {name} » existe déjà.")
    return Court.objects.create(name=name)


def update_court(court, name):
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom du court est requis.")
    if Court.objects.filter(name__iexact=name).exclude(pk=court.pk).exists():
        raise ValueError(f"Un court nommé « {name} » existe déjà.")
    court.name = name
    court.save()
    return court


def delete_court(court):
    """SET_NULL : suppression non bloquante, SAUF si un match ordonné y est attaché
    (la contrainte court_required_when_ordered lèverait alors une IntegrityError)."""
    if Match.objects.filter(court=court, order_index__isnull=False).exists():
        raise ValueError(
            "Court utilisé par des matchs ordonnés (file). "
            "Retire-les de la file avant de le supprimer."
        )
    court.delete()


# ── Épreuves (Event = édition × catégorie) ─────────────────────────────────

def create_event(edition, category, group_size_default=4, qualified_per_group=2, notes=""):
    if Event.objects.filter(edition=edition, category=category).exists():
        raise ValueError(f"L'épreuve « {category.name} » existe déjà pour {edition.year}.")
    gsd = _as_choice_int(group_size_default, (3, 4), "La taille de poule par défaut")
    qpg = _as_choice_int(qualified_per_group, (1, 2), "Le nombre de qualifiés par poule")
    return Event.objects.create(
        edition=edition,
        category=category,
        group_size_default=gsd,
        qualified_per_group=qpg,
        notes=(notes or ""),
    )


def update_event(event, group_size_default=_NOCHANGE, qualified_per_group=_NOCHANGE, notes=_NOCHANGE, has_third_place=_NOCHANGE):
    if group_size_default is not _NOCHANGE:
        event.group_size_default = _as_choice_int(group_size_default, (3, 4), "La taille de poule par défaut")
    if qualified_per_group is not _NOCHANGE:
        event.qualified_per_group = _as_choice_int(qualified_per_group, (1, 2), "Le nombre de qualifiés par poule")
    if notes is not _NOCHANGE:
        event.notes = notes or ""
    if has_third_place is not _NOCHANGE:
        event.has_third_place = bool(has_third_place)
    event.save()
    return event


def delete_event(event):
    """CASCADE (inscriptions/poules/matchs/bracket). Refusé si des matchs sont LIVE ou terminés."""
    if Match.objects.filter(
        event=event, status__in=[Match.Status.LIVE, Match.Status.FINISHED]
    ).exists():
        raise ValueError("Impossible de supprimer une épreuve avec des matchs en cours ou terminés.")
    event.delete()


# ── PlayDay + Break (journées de jeu et pauses) ──────────────────────────────

def create_play_day(edition, date, start_time, target_end_time):
    if PlayDay.objects.filter(edition=edition, date=date).exists():
        raise ValueError(f"Une journée de jeu existe déjà pour la date {date}.")
    return PlayDay.objects.create(
        edition=edition,
        date=date,
        start_time=start_time,
        target_end_time=target_end_time,
    )


def update_play_day(play_day, *, date=_NOCHANGE, start_time=_NOCHANGE, target_end_time=_NOCHANGE):
    if date is not _NOCHANGE:
        if PlayDay.objects.filter(edition=play_day.edition, date=date).exclude(pk=play_day.pk).exists():
            raise ValueError(f"Une journée de jeu existe déjà pour la date {date}.")
        play_day.date = date
    if start_time is not _NOCHANGE:
        play_day.start_time = start_time
    if target_end_time is not _NOCHANGE:
        play_day.target_end_time = target_end_time
    play_day.save()
    return play_day


def delete_play_day(play_day):
    if Break.objects.filter(play_day=play_day).exists():
        raise ValueError(
            "Impossible de supprimer cette journée : elle contient des pauses. "
            "Supprimez d'abord les pauses."
        )
    active_matches = Match.objects.filter(
        edition=play_day.edition,
        order_index__isnull=False,
        scheduled_time__date=play_day.date,
        status__in=[Match.Status.SCHEDULED, Match.Status.LIVE],
    )
    if active_matches.exists():
        raise ValueError(
            "Impossible de supprimer cette journée : elle contient des matchs planifiés. "
            "Renvoyez d'abord les matchs vers la pile « à planifier »."
        )
    finished_matches = Match.objects.filter(
        edition=play_day.edition,
        order_index__isnull=False,
        scheduled_time__date=play_day.date,
        status=Match.Status.FINISHED,
    )
    if finished_matches.exists():
        raise ValueError(
            "Impossible de supprimer cette journée : elle contient des matchs terminés."
        )
    play_day.delete()


def create_break(play_day, order_index, duration_min, label):
    if duration_min <= 0:
        raise ValueError("La durée d'une pause doit être supérieure à 0.")
    return Break.objects.create(
        play_day=play_day,
        order_index=order_index,
        duration_min=duration_min,
        label=(label or "").strip() or "Pause",
    )


def update_break(brk, *, order_index=_NOCHANGE, duration_min=_NOCHANGE, label=_NOCHANGE):
    if order_index is not _NOCHANGE:
        brk.order_index = order_index
    if duration_min is not _NOCHANGE:
        if duration_min <= 0:
            raise ValueError("La durée d'une pause doit être supérieure à 0.")
        brk.duration_min = duration_min
    if label is not _NOCHANGE:
        brk.label = (label or "").strip() or "Pause"
    brk.save()
    return brk


def delete_break(brk):
    brk.delete()


# ── Sprint 07 — Reorder calendrier évolué ─────────────────────────────────────

def reorder_calendar(edition, play_day_sequences):
    """
    Réordonne le calendrier de l'édition à partir d'une liste de séquences par journée.

    play_day_sequences : [{"playDayId": int, "items": [{"type": "match"|"break", "id": int}]}]

    - Chaque match reçoit un order_index global unique à l'édition + scheduled_time dont la
      date = celle de la journée (temps = start_time de la journée, ETA approximative).
    - Chaque Break reçoit un order_index local = sa position dans la séquence de la journée.
    - Les matchs absents de toute journée perdent order_index et scheduled_time.
    - Les matchs LIVE et FINISHED ne sont jamais déplacés : order_index persiste.
    """
    edition_play_days = {pd.id: pd for pd in PlayDay.objects.filter(edition=edition)}
    default_court = Court.objects.order_by("id").first()

    # Matchs déplaçables : uniquement SCHEDULED (pas LIVE, pas FINISHED, pas CANCELED) —
    # order_index persiste à travers LIVE/FINISHED (cf. specs/technical/planning.md).
    movable_statuses = [Match.Status.SCHEDULED]
    movable_qs = Match.objects.filter(edition=edition, status__in=movable_statuses)
    edition_matches = {m.id: m for m in movable_qs.select_for_update()}

    # Indices déjà utilisés par les matchs non-déplaçables (LIVE, FINISHED)
    used_indices = set(
        Match.objects.filter(edition=edition, order_index__isnull=False)
        .exclude(id__in=edition_matches.keys())
        .values_list("order_index", flat=True)
    )

    # Étape 1 : effacer tous les order_index des matchs déplaçables (évite les conflits d'unicité)
    movable_qs.update(order_index=None)

    global_idx = 1
    placed = {}  # match_id → (order_index, scheduled_dt)

    for day_spec in play_day_sequences:
        pd_id = int(day_spec.get("playDayId", 0))
        pd = edition_play_days.get(pd_id)
        if pd is None:
            raise ValueError(f"PlayDay {pd_id} n'appartient pas à cette édition.")

        items = day_spec.get("items", [])
        local_tz = timezone.get_current_timezone()
        scheduled_dt = timezone.make_aware(
            datetime.datetime.combine(pd.date, pd.start_time), local_tz
        )

        day_breaks = {b.id: b for b in Break.objects.filter(play_day=pd).select_for_update()}
        slot = 0

        for item in items:
            item_type = item.get("type")
            item_id = int(item.get("id", 0))

            if item_type == "match":
                m = edition_matches.get(item_id)
                if m is not None:
                    while global_idx in used_indices:
                        global_idx += 1
                    placed[item_id] = (global_idx, scheduled_dt)
                    used_indices.add(global_idx)
                    global_idx += 1

            elif item_type == "break":
                brk = day_breaks.get(item_id)
                if brk is not None:
                    brk.order_index = slot
                    brk.save(update_fields=["order_index"])

            slot += 1

    # Étape 2 : appliquer les placements
    for mid, (idx, scheduled_dt) in placed.items():
        m = edition_matches[mid]
        m.order_index = idx
        m.scheduled_time = scheduled_dt
        update_fields = ["order_index", "scheduled_time"]
        if m.court_id is None:
            if default_court is None:
                raise ValueError("Aucun court disponible. Crée un court avant d'ordonner les matchs.")
            m.court = default_court
            update_fields.append("court")
        m.save(update_fields=update_fields)

    # Étape 3 : matchs non placés → effacer scheduled_time (order_index déjà NULL depuis étape 1)
    for mid, m in edition_matches.items():
        if mid not in placed:
            m.scheduled_time = None
            m.save(update_fields=["scheduled_time"])


# ── Sprint 07 — Auto-arrange (pré-pose) ───────────────────────────────────────

def _entry_ids(match):
    """Retourne l'ensemble des Entry.id impliqués dans un match."""
    ids = set()
    if match.side_a_id:
        ids.add(match.side_a_id)
    if match.side_b_id:
        ids.add(match.side_b_id)
    return ids


def auto_arrange_matches(edition, default_duration_min=None):
    """
    Range automatiquement les matchs « à planifier » (SCHEDULED, order_index=None,
    stage=GROUP) sur les journées de l'édition, sans toucher aux matchs déjà placés.

    Algorithme (spec § Heuristique de pré-pose) :
    1. Entrelacement des poules (A, B, C, A, B, C…)
    2. Règle de repos : ≥ 1 match entre deux matchs d'une même Entry (best-effort, 1 passe)
    3. Distribution sur les journées dans l'ordre, selon la capacité (target_end_time)

    Retourne le nombre de matchs placés.
    """
    if default_duration_min is None:
        default_duration_min = edition.default_match_duration_min
    play_days = list(
        PlayDay.objects.filter(edition=edition)
        .prefetch_related("breaks")
        .order_by("date")
    )
    if not play_days:
        return 0

    unscheduled = list(
        Match.objects.filter(
            edition=edition,
            status=Match.Status.SCHEDULED,
            order_index__isnull=True,
            stage=Match.Stage.GROUP,
            group__isnull=False,
        ).order_by("event_id", "group_id", "id")
    )
    if not unscheduled:
        return 0

    # 1. Grouper par poule
    buckets: dict = defaultdict(list)
    for m in unscheduled:
        buckets[m.group_id].append(m)

    # 2. Entrelacement round-robin
    buckets_list = list(buckets.values())
    interleaved = []
    max_len = max(len(b) for b in buckets_list)
    for i in range(max_len):
        for bucket in buckets_list:
            if i < len(bucket):
                interleaved.append(bucket[i])

    # 3. Règle de repos : 1 passe de correction par swap
    for i in range(len(interleaved) - 1):
        if _entry_ids(interleaved[i]) & _entry_ids(interleaved[i + 1]):
            if i + 2 < len(interleaved):
                if not (_entry_ids(interleaved[i]) & _entry_ids(interleaved[i + 2])):
                    interleaved[i + 1], interleaved[i + 2] = interleaved[i + 2], interleaved[i + 1]

    # 4. Distribution sur les journées
    default_court = Court.objects.order_by("id").first()
    if not default_court:
        raise ValueError("Aucun court disponible. Crée un court avant d'utiliser la pré-pose.")
    max_idx = Match.objects.filter(
        edition=edition, order_index__isnull=False
    ).aggregate(m=Max("order_index"))["m"] or 0
    global_idx = max_idx + 1

    local_tz = timezone.get_current_timezone()
    from collections import deque
    pile = deque(interleaved)
    placed_count = 0

    for pd in play_days:
        if not pile:
            break

        placed_in_day_count = Match.objects.filter(
            edition=edition,
            order_index__isnull=False,
            scheduled_time__date=pd.date,
        ).count()
        breaks_duration = sum(b.duration_min for b in pd.breaks.all())
        used_minutes = placed_in_day_count * default_duration_min + breaks_duration

        start_dt = datetime.datetime.combine(pd.date, pd.start_time)
        end_dt = datetime.datetime.combine(pd.date, pd.target_end_time)
        capacity_minutes = int((end_dt - start_dt).total_seconds() // 60)

        scheduled_dt = timezone.make_aware(
            datetime.datetime.combine(pd.date, pd.start_time), local_tz
        )

        while pile and (used_minutes + default_duration_min) <= capacity_minutes:
            m = pile.popleft()
            m.order_index = global_idx
            m.scheduled_time = scheduled_dt
            update_fields = ["order_index", "scheduled_time"]
            if m.court_id is None:
                m.court = default_court
                update_fields.append("court")
            m.save(update_fields=update_fields)
            global_idx += 1
            used_minutes += default_duration_min
            placed_count += 1

    return placed_count

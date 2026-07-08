import random
import datetime
from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from core.models import TournamentEdition, Player, Team
from competition.models import Category, Event, Entry, Group, GroupMembership, GroupStanding
from live.models import Match, Court, PlayDay, Break, Announcement

from django import forms
from django.contrib.auth.decorators import user_passes_test


def superuser_required(view):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser)(view)


# -----------------------
# Forms
# -----------------------

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["first_name", "last_name", "gender", "birth_year", "phone", "email", "license_number", "attitude"]
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "gender": "Sexe",
            "birth_year": "Année de naissance",
            "phone": "Téléphone",
            "email": "Email",
            "license_number": "Numéro de licence",
            "attitude": "Attitude (pour les affiches)",
        }


class MatchEditForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            # Gestion
            "status", "order_index", "is_featured",

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
            "order_index": "Ordre (file)",
            "is_featured": "Mis en avant (TV)",

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

        if "order_index" in self.fields:
            self.fields["order_index"].disabled = True
            self.fields["order_index"].help_text = "Géré dans le panel Matchs."

    def clean(self):
        cleaned = super().clean()
        inst = self.instance
        fmt = cleaned.get("match_format")

        if cleaned.get("status") == Match.Status.FINISHED and not cleaned.get("winner_side"):
            self.add_error(None, "Un match Terminé doit avoir un vainqueur (Vainqueur : A ou B).")

        # is_featured : seule la transition vers False est acceptée par ce form
        # (extinction depuis le panneau d'édition). L'activation reste réservée à
        # start_match()/api_match_feature, qui gèrent l'invariant mono-LIVE
        # (rétrogradation des autres matchs featured) — cf.
        # specs/technical/cycle-de-vie-match.md. Toute tentative de passer
        # False -> True par ce form est ignorée silencieusement.
        if cleaned.get("is_featured") and not (inst and inst.pk and inst.is_featured):
            cleaned["is_featured"] = False

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


# -----------------------
# Actions : Players / Teams
# -----------------------

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


# Validation upload photo joueur (sprint 24, ticket #268)
ALLOWED_PHOTO_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024  # 10 Mo


def set_player_photo(player, uploaded_file):
    """
    Remplace la photo d'un joueur par le fichier uploadé (multipart).
    Purge l'ancien fichier physique s'il existe. Valide le format (jpg/jpeg/png/webp,
    via content_type) et la taille (<= 10 Mo).
    Lève ValueError si invalide (message utilisateur, à renvoyer tel quel en JSON).
    """
    if uploaded_file.size > MAX_PHOTO_SIZE_BYTES:
        raise ValueError("La photo dépasse la taille maximale autorisée (10 Mo).")

    content_type = getattr(uploaded_file, "content_type", "") or ""
    if content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
        raise ValueError("Format non supporté (jpg, jpeg, png ou webp uniquement).")

    old_photo = player.photo
    player.photo = uploaded_file
    player.save(update_fields=["photo"])

    if old_photo and old_photo.name:
        old_photo.storage.delete(old_photo.name)

    return player


def clear_player_photo(player):
    """
    Supprime la photo d'un joueur (purge du fichier physique + vidage du champ).
    No-op silencieux si le joueur n'a pas de photo.
    """
    old_photo = player.photo
    if old_photo and old_photo.name:
        old_photo.storage.delete(old_photo.name)
    player.photo = None
    player.save(update_fields=["photo"])
    return player


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
    from live.bracket import ensure_final_bracket_exists

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

def finalize_match_edit(match, was_live: bool = False, was_finished: bool = False):
    """
    Service : logique post-sauvegarde commune à l'édition d'un match
    (sanitisation des valeurs négatives, cohérence du tie-break, retrait
    featured/file si terminé, puis recalcul des classements de poule et
    synchronisation du tableau — mêmes effets que le chemin arbitre,
    cf. specs/technical/cycle-de-vie-match.md).
    Le match est supposé déjà passé par MatchEditForm.save().

    `was_live` : statut LIVE du match *avant* l'édition (déterminé par l'appelant
    avant que le form ne mute l'instance). Si le form vient de faire passer le
    match à LIVE alors qu'il ne l'était pas avant, on route vers start_match()
    (ou reopen_match() si le match était FINISHED, cf. `was_finished`) plutôt que
    de laisser le statut brut posé par le form, afin de préserver l'invariant
    mono-LIVE (rétrogradation des autres matchs + is_featured + started_at —
    cf. specs/technical/cycle-de-vie-match.md).

    `was_finished` : statut FINISHED du match *avant* l'édition (déterminé par
    l'appelant, comme `was_live`). Permet de distinguer une reprise depuis
    SCHEDULED (start_match) d'une réouverture depuis FINISHED (reopen_match).

    Retourne le match.
    """
    if match.status == Match.Status.LIVE and not was_live:
        # invariant mono-LIVE : router vers start_match()/reopen_match() plutôt que
        # de laisser le form poser le statut brut (cf. specs/technical/cycle-de-vie-match.md).
        if was_finished:
            reopen_match(match)
        else:
            match.status = Match.Status.SCHEDULED
            match.winner_side = None
            match.save()
            start_match(match)
            if match.stage == Match.Stage.GROUP and match.group_id:
                from competition.standings import recalc_one_group
                recalc_one_group(match.group_id)
        return match

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
        match.winner_side = None

    match.save()

    # Recalcul inconditionnel : une correction, une annulation ou une réouverture
    # changent aussi le classement (recalc_one_group resynchronise le bracket).
    if match.stage == Match.Stage.GROUP and match.group_id:
        from competition.standings import recalc_one_group
        recalc_one_group(match.group_id)

    if match.status == Match.Status.FINISHED and match.stage in (Match.Stage.QF, Match.Stage.SF):
        from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
        sync_final_winners_for_event(match.event)
        sync_p3_losers_for_event(match.event)

    if match.status == Match.Status.FINISHED and match.stage == Match.Stage.F:
        try:
            close_event(match.event)
        except ValueError:
            pass

    return match


def start_match(match):
    """
    Service : démarre un match (SCHEDULED -> LIVE), le met en avant TV.
    Réutilisé par referee_action('start') et par l'API admin.
    Idempotent : si le match est déjà LIVE, no-op (pas de re-déclenchement de la
    rétrogradation des autres matchs ni du featured).
    Retire is_featured des autres matchs de l'edition, met is_featured=True,
    puis mark_live() (status=LIVE + started_at si vide). Ne touche jamais
    order_index (persistance calendrier — sprint 15 / #159).
    Retourne le match.
    """
    if match.status == Match.Status.LIVE:
        return match

    if match.side_a_id is None or match.side_b_id is None:
        raise ValueError("Les deux joueurs doivent être connus avant de démarrer le match.")

    Match.objects.filter(edition=match.edition, is_featured=True).update(is_featured=False)
    match.is_featured = True
    match.mark_live()  # met status=LIVE + started_at si besoin
    match.save()
    return match


# Alias historique : conservé pour ne pas casser les appelants existants
# (match_feature / api_match_feature — action « mettre en avant » côté admin,
# effet identique à « démarrer »).
feature_match = start_match


@transaction.atomic
def reopen_match(match):
    """
    Service : rouvre un match terminé (FINISHED -> LIVE), ADMIN uniquement.
    Réutilisé par referee_action('reopen') et par finalize_match_edit()
    (panneau d'édition admin) — cf. specs/technical/cycle-de-vie-match.md, § « Rouvrir ».

    Conserve set_scores et l'historique (aucun champ de score n'est touché).
    Retire is_featured des autres matchs de l'édition, met ce match en avant,
    réinitialise winner_side, puis mark_live() (status=LIVE + started_at si vide,
    rétrogradation de l'éventuel autre match LIVE — invariant mono-LIVE).
    Ne touche jamais order_index (persistance calendrier — sprint 15 / #159).

    Retourne le match.
    """
    Match.objects.filter(edition=match.edition, is_featured=True).update(is_featured=False)
    match.is_featured = True
    match.winner_side = None
    match.mark_live()  # repasse LIVE (+ started_at si besoin), conserve set_scores
    match.save(update_fields=["is_featured", "winner_side"])

    if match.stage == Match.Stage.GROUP and match.group_id:
        from competition.standings import recalc_one_group
        recalc_one_group(match.group_id)

    return match


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
    Refuse (ValueError) si l'épreuve est débutée (retrait sec réservé à
    la phase INSCRIPTION) ou si l'Entry est déjà engagée dans un match.
    """
    if event.status != Event.Status.INSCRIPTION:
        raise ValueError(
            f"Impossible de retirer {entry} : l'épreuve est débutée "
            "(utiliser le forfait/retrait en cours de jeu)."
        )
    used_in_matches = Match.objects.filter(event=event, side_a=entry).exists() or \
        Match.objects.filter(event=event, side_b=entry).exists()
    if used_in_matches:
        raise ValueError(
            f"Impossible de retirer {entry} : déjà utilisé dans un ou plusieurs matchs."
        )
    entry.delete()


@transaction.atomic
def withdraw_entry(entry, remove_from_group=False):
    """
    Service : déclare le forfait d'une Entry (EN_COURS requis).
    - Pose entry.withdrawn = True.
    - Tous les matchs non terminés (SCHEDULED/LIVE) → FINISHED, is_walkover=True,
      winner_side = adversaire, score de convention (games_to_win / 0).
    - Si remove_from_group : supprime en plus le GroupMembership de l'entry
      (retrait de l'affichage poule, standings recalculés sans elle) — c'est
      le « retrait sans remplaçant » de la spec, distinct du simple forfait.
    - Recalcule les standings de chaque poule affectée.
    - Propage les vainqueurs du tableau (QF/SF/F) et les perdants des demies (P3).
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

    if remove_from_group:
        membership_group_ids = list(
            GroupMembership.objects.filter(entry=entry).values_list("group_id", flat=True)
        )
        affected_groups.update(membership_group_ids)
        GroupMembership.objects.filter(entry=entry).delete()

    for gid in affected_groups:
        recalc_one_group(gid)

    if affected_groups:
        from live.bracket import sync_final_bracket_for_event
        sync_final_bracket_for_event(event)

    if has_qf_sf:
        from live.bracket import sync_final_winners_for_event, sync_p3_losers_for_event
        sync_final_winners_for_event(event)
        sync_p3_losers_for_event(event)

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


def _final_matches_qs(event):
    return Match.objects.filter(
        event=event,
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
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
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
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
        stage__in=[Match.Stage.QF, Match.Stage.SF, Match.Stage.F, Match.Stage.P3],
    )

    if match.status != Match.Status.SCHEDULED:
        raise ValueError("Match déjà lancé.")

    if side == "A":
        match.side_a = None
        match.save(update_fields=["side_a"])
    else:
        match.side_b = None
        match.save(update_fields=["side_b"])


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

def create_edition(name, year, start_dt=None, end_dt=None):
    """Crée une édition. `year` unique. start/end_dt = datetime|None déjà parsés.
    Devient active automatiquement si aucune édition active n'existe (1er lancement)."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom de l'édition est requis.")
    year = _parse_year(year)
    if TournamentEdition.objects.filter(year=year).exists():
        raise ValueError(f"Une édition existe déjà pour l'année {year}.")
    is_first_active = not TournamentEdition.objects.filter(is_active=True).exists()
    edition = TournamentEdition(
        name=name,
        year=year,
        start_dt=start_dt or None,
        end_dt=end_dt or None,
        is_active=is_first_active,
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
            "Impossible de supprimer cette journée : des matchs y ont été joués. "
            "Une journée jouée est conservée comme archive."
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


# ── Sprint 22 — CRUD Announcement ─────────────────────────────────────────────

def create_announcement(edition, message, is_active=True):
    message = (message or "").strip()
    if not message:
        raise ValueError("Le message de l'annonce ne peut pas être vide.")
    return Announcement.objects.create(
        edition=edition,
        message=message,
        is_active=bool(is_active),
    )


def update_announcement(announcement, *, message=_NOCHANGE, is_active=_NOCHANGE):
    if message is not _NOCHANGE:
        message = (message or "").strip()
        if not message:
            raise ValueError("Le message de l'annonce ne peut pas être vide.")
        announcement.message = message
    if is_active is not _NOCHANGE:
        announcement.is_active = bool(is_active)
    announcement.save()
    return announcement


def delete_announcement(announcement):
    announcement.delete()

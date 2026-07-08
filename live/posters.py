"""
Module partagé de génération d'affiches de match (IA).

Ce module est la SEULE source de vérité pour :
- la construction du prompt envoyé à l'API OpenAI Images (`build_prompt`),
  importée par le CLI `scripts/generate_match_poster.py` — pas de copie
  locale du prompt ailleurs ;
- le pilotage du cycle de vie d'un `PosterJob` (thread de génération,
  sélection d'une candidate, retrait d'une affiche).

Pas de Celery dans le projet : la génération tourne dans un
`threading.Thread` daemon, piloté par polling côté front (endpoints `/api/`
hors scope de ce ticket — voir #266).
"""
from __future__ import annotations

import base64
import os
import random
import threading
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

from live.models import Match, PosterJob


# ── Prompt (extrait de scripts/generate_match_poster.py — source unique) ────

def player_label(sex: str) -> str:
    """
    Détermine le libellé ("joueur"/"joueuse") à partir d'un code sexe.

    Accepte à la fois les libellés texte historiques du CLI ("femme",
    "homme"...) et les codes `Player.Gender` ("F", "M", "O") pour permettre
    un appel direct avec `player.gender`.
    """
    normalized = (sex or "").strip().lower()

    if normalized in {"f", "femme", "féminin", "feminin", "joueuse", "fille"}:
        return "joueuse"

    if normalized in {"h", "m", "homme", "masculin", "joueur", "garçon", "garcon"}:
        return "joueur"

    return "joueur ou joueuse"


def build_prompt(names: list[str], sexes: list[str], adjectives: list[str]) -> str:
    """
    Construit le prompt "affiche de jeu de combat arcade" envoyé à
    `images.edit`. Contraintes conservées (spec affiche-match.md) :
    - le seul texte autorisé sur l'affiche est le titre du duel ;
    - la zone basse (25-30 % de la hauteur) reste libre pour le score ;
    - les adjectifs d'attitude ne doivent jamais être écrits sur l'affiche.
    """
    players = []

    for index, (name, sex, adjective) in enumerate(zip(names, sexes, adjectives), start=1):
        players.append({
            "index": index,
            "name": name.strip(),
            "label": player_label(sex),
            "adjective": adjective.strip(),
        })

    if len(players) == 2:
        confrontation = f"{players[0]['name']} contre {players[1]['name']}"
        composition = (
            "Affiche en duel : un joueur à gauche, l'autre à droite, "
            "séparés par un effet de choc lumineux au centre."
        )
        title = f"{players[0]['name']} VS {players[1]['name']}"
    else:
        confrontation = (
            f"{players[0]['name']} et {players[1]['name']} "
            f"contre {players[2]['name']} et {players[3]['name']}"
        )
        composition = (
            "Affiche de double : l'équipe 1 avec les deux premiers joueurs à gauche, "
            "l'équipe 2 avec les deux joueurs suivants à droite. "
            "Créer une vraie opposition visuelle entre les deux équipes."
        )
        title = (
            f"{players[0]['name']} & {players[1]['name']} "
            f"VS {players[2]['name']} & {players[3]['name']}"
        )

    descriptions = "\n".join(
        f"- Rends {p['name']} {p['adjective']}. "
        f"{p['name']} est la personne de l'image {p['index']}, {p['label']}. "
        f"Cette personnalité doit se voir dans son regard, son expression du visage, "
        f"sa posture, sa façon de tenir la raquette, son énergie et sa mise en scène. "
        f"Le mot « {p['adjective']} » ne doit jamais être écrit sur l'affiche."
        for p in players
    )

    adjectifs_interdits = ", ".join(f"« {p['adjective']} »" for p in players)

    prompt = f"""
Créer une affiche horizontale spectaculaire pour un match de tennis : {confrontation}.

Style visuel :
- affiche de jeu de combat arcade des années 90 ;
- ambiance Street Fighter / match de catch / affiche de combat sportif ;
- très dynamique, contrastée, cinématique ;
- terrain de tennis ou éléments de tennis visibles ;
- raquettes, balles, filet, lignes de court, énergie visuelle ;
- rendu moderne, propre, impression affiche événementielle.

Composition :
{composition}

Chaque joueur doit avoir une personnalité très marquée, presque caricaturale, comme dans une affiche de jeu de combat.
Les attitudes doivent être exagérées et immédiatement lisibles.

Direction artistique des joueurs à partir des images fournies :
{descriptions}

Important :
- les adjectifs sont des consignes de jeu, d'attitude et de mise en scène ;
- ils doivent être visibles dans le comportement des joueurs ;
- ils ne doivent jamais être écrits comme du texte sur l'affiche.

Contraintes très importantes sur le texte :
- le texte principal autorisé est uniquement : "{title}" ;
- tu peux ajouter en petit : "TOURNOI DES MOUTILLOUX" ;
- ne jamais écrire les adjectifs des joueurs sur l'affiche ;
- ne pas écrire ces mots : {adjectifs_interdits} ;
- ne pas écrire de score ;
- ne pas ajouter de date, d'heure, de slogan ou de phrase inventée ;
- ne pas ajouter de pseudo-texte illisible ;
- ne pas inventer de faux logos officiels ;
- ne rien écrire dans la zone basse réservée au score.

Format :
- affiche horizontale, format paysage ;
- composition pensée pour un affichage web en direct pendant un match ;
- les joueurs doivent être principalement dans la moitié haute et au centre gauche / centre droit ;
- le titre "{title}" doit être placé dans la moitié haute ou au centre, mais pas dans la zone basse réservée au score ;
- réserver toute la partie basse de l'image, environ 25 à 30 % de la hauteur, comme zone libre pour afficher le score en direct ;
- dans cette zone basse, ne mettre aucun visage, aucune main, aucune raquette importante, aucun texte important ;
- la zone basse doit être visuellement propre, sombre ou légèrement dégradée, avec éventuellement le terrain de tennis en arrière-plan ;
- cette zone basse doit pouvoir recevoir un score affiché par-dessus sans cacher les joueurs ;
- ne pas écrire le score dans l'image ;
- image finale propre, spectaculaire, amusante, prête pour un live web.
""".strip()

    return prompt


# ── Résolution des joueurs d'un match ────────────────────────────────────────

def resolve_match_players(match: Match) -> list:
    """
    Résout les joueurs concernés par un match à partir de `side_a`/`side_b`
    (chacun un `Entry`). Renvoie une liste ordonnée de `Player` :
    - 2 joueurs en simple (`entry.player`) ;
    - 4 joueurs en double (`entry.team.player1`, `entry.team.player2`),
      side_a puis side_b.

    Lève `ValueError` si un side est absent ou mal formé (ni player, ni team).
    """
    if match.side_a_id is None or match.side_b_id is None:
        raise ValueError("Les deux camps du match doivent être renseignés.")

    players = []

    for side in (match.side_a, match.side_b):
        if side.player_id:
            players.append(side.player)
        elif side.team_id:
            players.append(side.team.player1)
            players.append(side.team.player2)
        else:
            raise ValueError(f"Le camp « {side} » n'a ni joueur ni équipe.")

    return players


# ── Cycle de vie du PosterJob ─────────────────────────────────────────────

CANDIDATES_SUBDIR = "match_posters/candidates"


def _purge_job(job: PosterJob) -> None:
    """
    Supprime les fichiers candidats physiques du job (silencieux si déjà
    absents) puis la ligne `PosterJob` elle-même.
    """
    media_root = Path(settings.MEDIA_ROOT)

    for relative_path in (job.candidate_paths or []):
        file_path = media_root / relative_path
        try:
            file_path.unlink()
        except FileNotFoundError:
            pass

    job.delete()


def start_poster_job(match: Match, attitudes: dict) -> PosterJob:
    """
    Démarre une génération d'affiche pour `match` avec les attitudes fournies
    (`{"A": "...", "B": "..."}` ou `{"A1": "...", ...}` en double — les clés
    exactes sont à la charge de l'appelant, seules les valeurs sont utilisées
    dans l'ordre des joueurs résolus).

    Gardes (échouent avec `ValueError` avant toute création) :
    - les deux sides résolus (`resolve_match_players`) ;
    - chaque joueur concerné a une photo ;
    - `OPENAI_API_KEY` présent dans l'environnement ;
    - pas de job déjà `RUNNING` pour ce match.

    Purge un job précédent non-RUNNING pour ce match avant d'en créer un
    nouveau. Retourne le `PosterJob` créé (état PENDING/RUNNING au retour —
    la génération continue en tâche de fond dans un thread).
    """
    players = resolve_match_players(match)

    for player in players:
        if not player.photo:
            raise ValueError(
                f"Le joueur {player} n'a pas de photo : impossible de générer l'affiche."
            )

    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "La variable d'environnement OPENAI_API_KEY n'est pas définie sur le serveur."
        )

    existing = PosterJob.objects.filter(match=match).order_by("-created_at").first()
    if existing is not None:
        if existing.status == PosterJob.Status.RUNNING:
            raise ValueError("Une génération est déjà en cours pour ce match.")
        _purge_job(existing)

    job = PosterJob.objects.create(
        match=match,
        status=PosterJob.Status.PENDING,
        attitudes=attitudes or {},
    )

    thread = threading.Thread(target=_run_poster_job, args=(job.pk,), daemon=True)
    thread.start()

    return job


def _run_poster_job(job_id: int) -> None:
    """
    Corps du thread de génération. Ferme les connexions DB héritées du
    thread principal avant toute requête ORM (piège Django + threads).
    """
    from django import db
    db.connections.close_all()

    from openai import OpenAI

    job = PosterJob.objects.select_related("match").get(pk=job_id)

    try:
        job.status = PosterJob.Status.RUNNING
        job.save(update_fields=["status"])

        match = job.match
        players = resolve_match_players(match)
        attitudes = job.attitudes or {}
        attitude_values = list(attitudes.values()) if attitudes else []

        names = [str(p) for p in players]
        sexes = [p.gender for p in players]

        if len(attitude_values) == len(players):
            adjectives = attitude_values
        else:
            adjectives = [
                random.choice(p.attitudes) if p.attitudes else "déterminé"
                for p in players
            ]

        prompt = build_prompt(names, sexes, adjectives)

        opened_files = [player.photo.open("rb") for player in players]
        try:
            client = OpenAI()
            result = client.images.edit(
                model="gpt-image-2",
                image=opened_files,
                prompt=prompt,
                n=2,
                size="1536x1024",
                quality="medium",
                output_format="png",
            )
        finally:
            for f in opened_files:
                f.close()

        candidates_dir = Path(settings.MEDIA_ROOT) / CANDIDATES_SUBDIR
        candidates_dir.mkdir(parents=True, exist_ok=True)

        candidate_paths = []
        for index, image_data in enumerate(result.data, start=1):
            if not image_data.b64_json:
                raise RuntimeError("L'API n'a pas renvoyé d'image en base64.")

            image_bytes = base64.b64decode(image_data.b64_json)
            filename = f"job{job.pk}_{index}_{uuid.uuid4().hex[:8]}.png"
            file_path = candidates_dir / filename
            file_path.write_bytes(image_bytes)

            candidate_paths.append(f"{CANDIDATES_SUBDIR}/{filename}")

        job.candidate_paths = candidate_paths
        job.status = PosterJob.Status.DONE
        job.save(update_fields=["candidate_paths", "status"])

    except Exception as exc:
        job.status = PosterJob.Status.ERROR
        job.error = str(exc)
        job.save(update_fields=["status", "error"])


def select_poster_candidate(job: PosterJob, index: int) -> Match:
    """
    Retient la candidate `index` (0 ou 1) du job comme affiche du match :
    copie le fichier vers `Match.poster`, sauvegarde le match, puis purge le
    job et toutes les candidates (fichiers compris) — on ne garde que
    l'élue.
    """
    candidate_paths = job.candidate_paths or []

    if index not in (0, 1) or index >= len(candidate_paths):
        raise ValueError("Index de candidate invalide (attendu 0 ou 1).")

    media_root = Path(settings.MEDIA_ROOT)
    source_path = media_root / candidate_paths[index]

    if not source_path.exists():
        raise ValueError("Le fichier de la candidate sélectionnée est introuvable.")

    match = job.match
    filename = f"match_{match.pk}_{uuid.uuid4().hex[:8]}.png"

    with open(source_path, "rb") as f:
        match.poster.save(filename, ContentFile(f.read()), save=True)

    _purge_job(job)

    return match


def clear_poster(match: Match) -> Match:
    """Retire l'affiche retenue du match (supprime le fichier, vide le champ)."""
    if match.poster:
        match.poster.delete(save=False)
        match.poster = None
        match.save(update_fields=["poster"])

    return match

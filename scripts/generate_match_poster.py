#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES_PER_API_CALL = 10


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def guess_extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".jpg"

    mime = content_type.split(";")[0].strip().lower()
    extension = mimetypes.guess_extension(mime)

    if extension == ".jpe":
        return ".jpg"

    if extension in SUPPORTED_EXTENSIONS:
        return extension

    return ".jpg"


def download_image_to_temp(url: str, tmpdir: Path) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        suffix = guess_extension_from_content_type(response.headers.get("content-type"))

    file_path = tmpdir / f"{uuid.uuid4().hex}{suffix}"
    file_path.write_bytes(response.content)

    return file_path


def resolve_image_path(source: str, base_dir: Path | None, tmpdir: Path) -> Path:
    if is_url(source):
        return download_image_to_temp(source, tmpdir)

    path = Path(source)

    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path

    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"Image introuvable : {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Format non supporté pour {path}. "
            f"Formats attendus : {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        raise ValueError(f"L'image {path} fait {size_mb:.1f} Mo. Maximum conseillé : 50 Mo.")

    return path


def player_label(sex: str) -> str:
    normalized = sex.strip().lower()

    if normalized in {"f", "femme", "féminin", "feminin", "joueuse", "fille"}:
        return "joueuse"

    if normalized in {"h", "homme", "masculin", "joueur", "garçon", "garcon"}:
        return "joueur"

    return "joueur ou joueuse"


def build_prompt(names: list[str], sexes: list[str], adjectives: list[str]) -> str:
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


def generate_posters(
    image_sources: list[str],
    names: list[str],
    sexes: list[str],
    adjectives: list[str],
    output_dir: Path,
    count: int,
    base_dir: Path | None = None,
    public_prefix: str | None = None,
    model: str = "gpt-image-2",
    size: str = "1536x1024",
    quality: str = "medium",
) -> list[str]:
    if len(image_sources) not in {2, 4}:
        raise ValueError("Il faut fournir exactement 2 ou 4 images.")

    expected = len(image_sources)

    if not (len(names) == len(sexes) == len(adjectives) == expected):
        raise ValueError(
            "Le nombre de prénoms, de sexes et d'adjectifs doit correspondre au nombre d'images."
        )

    if count < 1:
        raise ValueError("Le nombre d'images demandé doit être supérieur ou égal à 1.")

    output_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    prompt = build_prompt(names, sexes, adjectives)

    references: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        image_paths = [
            resolve_image_path(source, base_dir=base_dir, tmpdir=tmpdir)
            for source in image_sources
        ]

        remaining = count
        batch_index = 1

        while remaining > 0:
            batch_count = min(remaining, MAX_IMAGES_PER_API_CALL)

            opened_files = [open(path, "rb") for path in image_paths]

            try:
                print(f"Envoi de la demande à OpenAI pour {batch_count} image(s)...", flush=True)

                result = client.images.edit(
                    model=model,
                    image=opened_files,
                    prompt=prompt,
                    n=batch_count,
                    size=size,
                    quality=quality,
                    output_format="png",
                )

                print("Réponse reçue. Enregistrement des images...", flush=True)
            finally:
                for file in opened_files:
                    file.close()

            for image_index, image_data in enumerate(result.data, start=1):
                if not image_data.b64_json:
                    raise RuntimeError("L'API n'a pas renvoyé d'image en base64.")

                image_bytes = base64.b64decode(image_data.b64_json)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"match_poster_{timestamp}_{batch_index}_{image_index}_{uuid.uuid4().hex[:8]}.png"
                file_path = output_dir / filename

                file_path.write_bytes(image_bytes)
                print(f"Image enregistrée : {file_path}", flush=True)

                if public_prefix:
                    ref = f"{public_prefix.rstrip('/')}/{filename}"
                else:
                    ref = str(file_path)

                references.append(ref)

            remaining -= batch_count
            batch_index += 1

    return references


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère une ou plusieurs affiches IA pour un match de tennis."
    )

    parser.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="2 ou 4 images. Ex: media/players/a.jpg media/players/b.jpg",
    )

    parser.add_argument(
        "--names",
        nargs="+",
        required=True,
        help="Prénoms des joueurs, dans le même ordre que les images.",
    )

    parser.add_argument(
        "--sexes",
        nargs="+",
        required=True,
        help="Sexe de chaque joueur. Ex: femme homme",
    )

    parser.add_argument(
        "--adjectives",
        nargs="+",
        required=True,
        help="Adjectif ou attitude de chaque joueur. Ex: charmeuse agressif",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Nombre d'images à générer.",
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Dossier de sortie des images générées.",
    )

    parser.add_argument(
        "--base-dir",
        default=None,
        help="Répertoire de base pour les chemins relatifs. Exemple : /home/cyrille/moutilloux",
    )

    parser.add_argument(
        "--public-prefix",
        default=None,
        help="Préfixe public à retourner. Exemple : /media/generated_match_posters",
    )

    parser.add_argument(
        "--model",
        default="gpt-image-2",
        help="Modèle image OpenAI.",
    )

    parser.add_argument(
        "--size",
        default="1536x1024",
        help="Taille de sortie. Exemple : 1536x1024 pour une affiche horizontale.",
    )

    parser.add_argument(
        "--quality",
        default="medium",
        choices=["low", "medium", "high", "auto"],
        help="Qualité de génération.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Erreur : la variable d'environnement OPENAI_API_KEY n'est pas définie.",
            file=sys.stderr,
        )
        return 1

    try:
        refs = generate_posters(
            image_sources=args.images,
            names=args.names,
            sexes=args.sexes,
            adjectives=args.adjectives,
            output_dir=Path(args.out),
            count=args.n,
            base_dir=Path(args.base_dir) if args.base_dir else None,
            public_prefix=args.public_prefix,
            model=args.model,
            size=args.size,
            quality=args.quality,
        )

        print(json.dumps({"images": refs}, ensure_ascii=False, indent=2))
        return 0

    except Exception as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

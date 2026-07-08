#!/usr/bin/env python3
"""
CLI de génération d'affiches de match (usage manuel / essais).

Ce script doit désormais être lancé depuis la racine du projet, avec
l'environnement Django du projet disponible (venv `_env`) : il importe
`build_prompt` depuis `live.posters`, seule source de vérité du prompt (voir
specs/technical/affiche-match.md). Un bootstrap Django minimal
(`django.setup()`) est fait ci-dessous avant cet import.
"""
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


def _bootstrap_django() -> None:
    """
    Configure Django au minimum pour pouvoir importer `live.posters`
    (module partagé du prompt). Le script doit être lancé depuis la racine
    du projet (là où se trouve `manage.py`).
    """
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moutilloux.settings")

    import django
    django.setup()


_bootstrap_django()

from live.posters import build_prompt  # noqa: E402  (après bootstrap Django)


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

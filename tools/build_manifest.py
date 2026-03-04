#!/usr/bin/env python3
"""
build_manifest.py

Creates a minimal portfolio project structure, copies audio files into a publishable assets folder
using stable generic IDs (w0001, w0002, ...), and generates site/works.json.

- We do NOT trust file names for metadata.
- We keep original extensions.
- We keep source paths for traceability.
- We avoid renaming based on dates/titles.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any, Tuple


# --- Configure project root (this script assumes it's located at <root>/tools/build_manifest.py) ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]

SITE_DIR = PROJECT_ROOT / "site"
ASSETS_DIR = PROJECT_ROOT / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"
IMAGES_DIR = ASSETS_DIR / "images"

MANIFEST_PATH = SITE_DIR / "works.json"

# --- Your current source file list (verbatim) ---
SOURCE_FILES: List[str] = [
    # Compositions + Sketches
    r"E:\Music Projects\Cubase\2023-08-12_DreamCompendium_No.2\Mixdown\2006_Theodoridis_DreamCompendium_No.2_24-bit_48kHz.wav",
    r"E:\Music Projects\Logic\18.09.02_Everlasting Three\Bounces\18.09.02_Everlasting Three.m4a",
    r"E:\Music Projects\Cubase\MusicML-Analysis\Mixdown\Study-in-16.mp3",
    r"E:\Documents\04_Projects\4.113_freqee_music_portfolio\28 Oct, 17.23_.mp3",
    r"E:\Music Projects\Cubase\21.09_TrioPoly(midi)\Mixdown\TrioImprov_Lament.mp3",
    r"E:\Music Projects\Cubase\improvpolyphony\Mixdown\20210829_ImprovPoly.mp3",
    r"E:\Music Projects\Cubase\21.11_OrthodoxChant\Mixdown\Orthodox Chant-like.mp3",

    # Studies + Interpretations / Systems
    r"E:\Music Projects\Cubase\22.10_Dame\Mixdown\22.10_Dame.mp3",
    r"E:\Music Projects\Cubase\Sylith-04\Mixdown\PusaunImprov.wav",
    r"E:\Music Projects\Cubase\Starling-04\Mixdown\Vedgalm.mp3",
    r"E:\Music Projects\Logic\17.05 Tant con je vivrai\Adam de la Halle – Tant con je vivrai (Sample).mp3",
    r"E:\Music Projects\Cubase\22.01_Morales_PieJesu\Mixdown\20220117_Morales_Misa-de-defuntos_Sequentia.mp3",
    r"E:\Music Projects\Cubase\2023-07-01_FaenzaCodex-Constantia\Mixdown\FaenzaCodex-Constantia.mp3",
    r"E:\Music Projects\Cubase\22.01_ScheinPadouana\Mixdown\ScheinPadouana(draft,1stphrase).mp3",
    r"E:\Music Projects\Cubase\shos_11_II_80\Mixdown\shos_11_II_80.wav",
    r"E:\Music Projects\Logic\18.08_Caserta_Demadolour\Bounces\18.08_Caserta_Demadolour.m4a",
    r"E:\Music Projects\Logic\Hasapiko Arrangement\Bounces\Hasapiko Arrangement.mp3",
    r"E:\Music Projects\Logic\20.10 Uppon la la laaa [THIS ONE!]\Bounces\20.10 Uppon la la laaa [THIS ONE!].wav",
]


@dataclass(frozen=True)
class WorkStub:
    id: str
    source_path: str
    published_audio: str
    ext: str
    size_bytes: int
    sha256_12: str


def ensure_dirs() -> None:
    for p in [SITE_DIR, AUDIO_DIR, IMAGES_DIR, PROJECT_ROOT / "tools"]:
        p.mkdir(parents=True, exist_ok=True)


def sha256_prefix(path: Path, n_hex: int = 12, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()[:n_hex]


def make_id(i: int) -> str:
    # Stable, generic, sortable, fixed width.
    return f"w{i:04d}"


def copy_if_needed(src: Path, dst: Path) -> None:
    # Avoid recopy if same size exists (fast check). We can extend later to hash compare.
    if dst.exists() and dst.stat().st_size == src.stat().st_size:
        return
    dst.write_bytes(src.read_bytes())


def build_stubs(source_files: Iterable[str]) -> List[WorkStub]:
    stubs: List[WorkStub] = []
    missing: List[str] = []

    for idx, src_str in enumerate(source_files, start=1):
        src = Path(src_str)
        if not src.exists():
            missing.append(src_str)
            continue

        wid = make_id(idx)
        ext = src.suffix.lower().lstrip(".")
        if not ext:
            # Unlikely, but we guard.
            ext = "bin"

        dst_name = f"{wid}.{ext}"
        dst = AUDIO_DIR / dst_name

        copy_if_needed(src, dst)

        size_bytes = dst.stat().st_size
        h12 = sha256_prefix(dst, 12)

        stubs.append(
            WorkStub(
                id=wid,
                source_path=src_str,
                published_audio=f"assets/audio/{dst_name}",
                ext=ext,
                size_bytes=size_bytes,
                sha256_12=h12,
            )
        )

    if missing:
        print("WARNING: Some source files were not found and were skipped:")
        for m in missing:
            print(f"  - {m}")

    return stubs


def make_manifest(stubs: List[WorkStub]) -> Dict[str, Any]:
    # Categories reflect the structure we agreed, but we keep metadata placeholders empty for now.
    return {
        "schema_version": 1,
        "artist": "FREQEE",
        "ui": {
            "primary_categories": [
                "compositions",
                "interpretations",
                "systems"
            ],
            "subcategories": {
                "compositions": ["works", "sketches"],
                "systems": ["sound_design", "instrument_systems"]
            }
        },
        "works": [
            {
                "id": s.id,
                "title": "",            # TODO: fill during curation
                "year": None,           # TODO
                "category": "",         # TODO: compositions | interpretations | systems
                "subcategory": None,    # TODO: works/sketches or sound_design/instrument_systems
                "description": "",      # TODO
                "tags": [],             # TODO
                "published_audio": s.published_audio,
                "image": None,          # TODO: assets/images/<id>.png etc.
                "source": {
                    "path": s.source_path,
                    "ext": s.ext,
                    "size_bytes": s.size_bytes,
                    "sha256_12": s.sha256_12
                }
            }
            for s in stubs
        ]
    }


def write_manifest(manifest: Dict[str, Any]) -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> None:
    ensure_dirs()
    stubs = build_stubs(SOURCE_FILES)
    manifest = make_manifest(stubs)
    write_manifest(manifest)

    print("OK")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Audio copied to: {AUDIO_DIR}")
    print(f"  Manifest written: {MANIFEST_PATH}")
    print("")
    print("Next: we will fill title/year/category/subcategory/description for each work id.")


if __name__ == "__main__":
    main()
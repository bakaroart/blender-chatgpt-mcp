#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "blender_addon" / "blender_chatgpt_bridge"
DIST_DIR = ROOT / "dist"
OUT = DIST_DIR / "blender_chatgpt_bridge.zip"

EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "tests", "previews"}


def include(path: Path) -> bool:
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    return True


def main() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in ADDON_DIR.rglob("*"):
            if path.is_file() and include(path):
                archive.write(path, Path("blender_chatgpt_bridge") / path.relative_to(ADDON_DIR))
    print(OUT)


if __name__ == "__main__":
    main()

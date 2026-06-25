#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def find_blender() -> str | None:
    override = os.environ.get("BLENDER_BIN")
    if override:
        return override

    blender = shutil.which("blender")
    if blender is not None:
        return blender

    for candidate in (
        "/Applications/Blender.app/Contents/MacOS/Blender",
        str(Path.home() / "Applications/Blender.app/Contents/MacOS/Blender"),
    ):
        if Path(candidate).is_file():
            return candidate

    return None


def main() -> int:
    load_env_file()
    blender = find_blender()
    if blender is None:
        print("Blender executable not found. Set BLENDER_BIN to the Blender executable path.")
        return 1
    if not os.environ.get("BLENDER_BRIDGE_TOKEN"):
        print("BLENDER_BRIDGE_TOKEN is required. Generate one in Blender or set it in .env.")
        return 1

    os.environ.setdefault("BLENDER_PROJECT_ROOT", str(ROOT))
    return subprocess.call(
        [
            blender,
            "--python",
            str(ROOT / "scripts" / "start_blender_bridge.py"),
        ],
        cwd=ROOT,
        env=os.environ.copy(),
    )


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    blender = find_blender()
    if blender is None:
        print(
            "Blender executable not found. Set BLENDER_BIN or run manually: "
            "blender --background --factory-startup --python blender_tests/smoke_test.py"
        )
        return 0
    return subprocess.call(
        [
            blender,
            "--background",
            "--factory-startup",
            "--python",
            str(ROOT / "blender_tests" / "smoke_test.py"),
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    sys.exit(main())

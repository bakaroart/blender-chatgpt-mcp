from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ADDON_PARENT = ROOT / "blender_addon"
sys.path.insert(0, str(ADDON_PARENT))

from blender_chatgpt_bridge import bridge_server


def main() -> None:
    token = os.environ.get("BLENDER_BRIDGE_TOKEN", "")
    if not token:
        raise RuntimeError("BLENDER_BRIDGE_TOKEN is required.")

    port = int(os.environ.get("BLENDER_BRIDGE_PORT", "8765"))
    project_root = os.environ.get("BLENDER_PROJECT_ROOT", str(ROOT))
    normal_timeout = float(os.environ.get("BLENDER_COMMAND_TIMEOUT_SEC", "30"))
    render_timeout = float(os.environ.get("BLENDER_RENDER_TIMEOUT_SEC", "120"))
    audit_log_path = os.environ.get("BLENDER_AUDIT_LOG_PATH") or None

    bridge_server.start_bridge(
        port,
        token,
        project_root,
        normal_timeout,
        render_timeout,
        audit_log_path,
    )
    print(f"Blender MCP bridge running on 127.0.0.1:{port}")


if __name__ == "__main__":
    main()

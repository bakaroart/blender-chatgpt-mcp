from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..path_sandbox import SafePathResolver
from ..protocol import BridgeError


def _bpy() -> Any:
    import bpy

    return bpy


def save_copy(args: dict[str, Any], context: Any) -> dict[str, Any]:
    bpy = _bpy()
    if not context.project_root:
        raise BridgeError("PROJECT_ROOT_NOT_CONFIGURED", "Project root is not configured.", status=409)
    resolver = SafePathResolver(context.project_root)
    target = resolver.resolve_new_file(args["relative_path"], create_directories=args.get("create_directories", False), suffix=".blend")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=bool(args.get("compress", True)), copy=True)
    except TypeError:
        current = bpy.data.filepath
        try:
            bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=bool(args.get("compress", True)))
        finally:
            if current:
                bpy.data.filepath = current
    except Exception as exc:
        raise BridgeError("BLENDER_CONTEXT_ERROR", "Unable to save a Blender file copy.", status=500, details={"type": type(exc).__name__}) from exc
    stat = target.stat()
    root = Path(context.project_root).resolve()
    return {
        "relative_path": target.resolve().relative_to(root).as_posix(),
        "size": stat.st_size,
        "timestamp": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
    }

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

from ..protocol import MAX_PREVIEW_BYTES, BridgeError


def _bpy() -> Any:
    import bpy

    return bpy


def _camera(name: str | None) -> Any:
    bpy = _bpy()
    if name:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "CAMERA":
            raise BridgeError("CAMERA_NOT_FOUND", f"Camera not found: {name}", status=409)
        return obj
    if bpy.context.scene.camera is None:
        raise BridgeError("CAMERA_NOT_FOUND", "No active camera is configured.", status=409)
    return bpy.context.scene.camera


def _snapshot(scene: Any) -> dict[str, Any]:
    render = scene.render
    image_settings = render.image_settings
    return {
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "filepath": render.filepath,
        "film_transparent": render.film_transparent,
        "file_format": image_settings.file_format,
        "quality": image_settings.quality,
        "camera": scene.camera,
        "engine": render.engine,
        "cycles_samples": getattr(getattr(scene, "cycles", None), "samples", None),
    }


def _restore(scene: Any, snapshot: dict[str, Any]) -> None:
    render = scene.render
    image_settings = render.image_settings
    render.resolution_x = snapshot["resolution_x"]
    render.resolution_y = snapshot["resolution_y"]
    render.filepath = snapshot["filepath"]
    render.film_transparent = snapshot["film_transparent"]
    image_settings.file_format = snapshot["file_format"]
    image_settings.quality = snapshot["quality"]
    scene.camera = snapshot["camera"]
    if snapshot["cycles_samples"] is not None and hasattr(scene, "cycles"):
        scene.cycles.samples = snapshot["cycles_samples"]


def _cleanup_stale(temp_dir: Path) -> None:
    now = time.time()
    for path in temp_dir.glob("preview-*"):
        try:
            if now - path.stat().st_mtime > 3600:
                path.unlink(missing_ok=True)
        except OSError:
            pass


def render_preview(args: dict[str, Any], context: Any) -> dict[str, Any]:
    bpy = _bpy()
    scene = bpy.context.scene
    camera = _camera(args.get("camera_name"))
    temp_dir = Path(context.temp_dir or Path.home() / ".cache" / "blender-mcp-bridge")
    temp_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_stale(temp_dir)
    suffix = ".jpg" if args["format"] == "jpeg" else ".png"
    target = temp_dir / f"preview-{time.time_ns()}{suffix}"
    snapshot = _snapshot(scene)
    started = time.monotonic()
    try:
        scene.camera = camera
        scene.render.resolution_x = args["width"]
        scene.render.resolution_y = args["height"]
        scene.render.filepath = str(target)
        scene.render.film_transparent = args.get("transparent_background", False)
        scene.render.image_settings.file_format = "JPEG" if args["format"] == "jpeg" else "PNG"
        scene.render.image_settings.quality = args["quality"]
        if hasattr(scene, "cycles"):
            scene.cycles.samples = args["samples"]
        bpy.ops.render.render(write_still=True)
        if not target.exists():
            raise BridgeError("RENDER_FAILED", "Preview file was not produced.", status=500)
        data = target.read_bytes()
        if len(data) > MAX_PREVIEW_BYTES and args["format"] == "jpeg":
            for quality in (70, 55, 40, 30):
                scene.render.image_settings.quality = quality
                bpy.ops.render.render(write_still=True)
                data = target.read_bytes()
                if len(data) <= MAX_PREVIEW_BYTES:
                    break
        if len(data) > MAX_PREVIEW_BYTES:
            raise BridgeError("RENDER_FAILED", "Preview image exceeded the 2 MB output limit.", status=500)
        mime_type = "image/jpeg" if args["format"] == "jpeg" else "image/png"
        return {
            "mime_type": mime_type,
            "width": args["width"],
            "height": args["height"],
            "byte_size": len(data),
            "render_duration_ms": int((time.monotonic() - started) * 1000),
            "camera_name": camera.name,
            "image_base64": base64.b64encode(data).decode("ascii"),
        }
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("RENDER_FAILED", "Preview render failed.", status=500, details={"type": type(exc).__name__}) from exc
    finally:
        _restore(scene, snapshot)
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass

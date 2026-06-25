from __future__ import annotations

from typing import Any

from ..protocol import BRIDGE_VERSION, MAX_SCENE_OBJECTS, PROTOCOL_VERSION
from ..serialization import object_summary


def _bpy() -> Any:
    import bpy

    return bpy


def _relative_blend_path(filepath: str, project_root: str | None) -> str | None:
    if not filepath:
        return None
    from pathlib import Path

    path = Path(filepath)
    if project_root:
        try:
            return path.resolve().relative_to(Path(project_root).resolve()).as_posix()
        except ValueError:
            return path.name
    return path.name


def get_status(_args: dict[str, Any], context: Any) -> dict[str, Any]:
    bpy = _bpy()
    scene = bpy.context.scene
    active_object = bpy.context.view_layer.objects.active
    active_camera = scene.camera
    filepath = bpy.data.filepath
    return {
        "bridge_version": BRIDGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "blender_version": bpy.app.version_string,
        "blend_filepath": _relative_blend_path(filepath, context.project_root),
        "has_unsaved_changes": bool(getattr(bpy.data, "is_dirty", False)),
        "active_scene": scene.name,
        "active_view_layer": bpy.context.view_layer.name,
        "current_frame": int(scene.frame_current),
        "render_engine": scene.render.engine,
        "object_count": len(bpy.data.objects),
        "active_object_name": active_object.name if active_object else None,
        "active_camera_name": active_camera.name if active_camera else None,
        "project_root_configured": bool(context.project_root),
    }


def get_scene_summary(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    scene = bpy.context.scene
    include_hidden = args.get("include_hidden", False)
    object_types = args.get("object_types")
    max_objects = min(int(args.get("max_objects", 100)), MAX_SCENE_OBJECTS)
    objects = []
    total_seen = 0
    for obj in scene.objects:
        if not include_hidden and not obj.visible_get():
            continue
        obj_type = str(obj.type).lower()
        if object_types and obj_type not in object_types:
            continue
        total_seen += 1
        if len(objects) < max_objects:
            objects.append(object_summary(obj, include_modifiers=False))
    world = scene.world
    return {
        "scene_name": scene.name,
        "frame": int(scene.frame_current),
        "unit_settings": {
            "system": scene.unit_settings.system,
            "scale_length": float(scene.unit_settings.scale_length),
        },
        "active_camera": scene.camera.name if scene.camera else None,
        "world": {
            "name": world.name if world else None,
            "color": list(world.color)[:3] if world else None,
        },
        "collections": [collection.name for collection in bpy.data.collections],
        "objects": objects,
        "truncated": total_seen > len(objects),
        "returned_objects": len(objects),
        "matching_objects": total_seen,
    }

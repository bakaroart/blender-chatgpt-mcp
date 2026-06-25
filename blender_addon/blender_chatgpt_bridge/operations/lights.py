from __future__ import annotations

from typing import Any

from ..protocol import BridgeError
from ..serialization import object_summary


def _bpy() -> Any:
    import bpy

    return bpy


def _ensure_no_object(name: str) -> None:
    if _bpy().data.objects.get(name) is not None:
        raise BridgeError("OBJECT_NAME_CONFLICT", f"Object already exists: {name}", status=409)


def _light_object(name: str) -> Any:
    obj = _bpy().data.objects.get(name)
    if obj is None:
        raise BridgeError("OBJECT_NOT_FOUND", f"Object not found: {name}", status=409)
    if obj.type != "LIGHT":
        raise BridgeError("INVALID_OBJECT_TYPE", "Object is not a light.", status=409)
    return obj


def _apply_light_settings(obj: Any, args: dict[str, Any]) -> None:
    data = obj.data
    for field in ("location", "rotation_euler"):
        if field in args:
            setattr(obj, field, args[field])
    if "energy" in args:
        data.energy = args["energy"]
    if "color" in args:
        data.color = args["color"]
    if "size" in args and hasattr(data, "size"):
        data.size = args["size"]
    if "radius" in args and hasattr(data, "shadow_soft_size"):
        data.shadow_soft_size = args["radius"]
    if "spot_size" in args and hasattr(data, "spot_size"):
        data.spot_size = args["spot_size"]
    if "spot_blend" in args and hasattr(data, "spot_blend"):
        data.spot_blend = args["spot_blend"]


def create_light(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    _ensure_no_object(args["name"])
    data = bpy.data.lights.new(args["name"], args["light_type"].upper())
    obj = bpy.data.objects.new(args["name"], data)
    bpy.context.scene.collection.objects.link(obj)
    _apply_light_settings(obj, args)
    return object_summary(obj)


def update_light(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _light_object(args["name"])
    _apply_light_settings(obj, args)
    return object_summary(obj)

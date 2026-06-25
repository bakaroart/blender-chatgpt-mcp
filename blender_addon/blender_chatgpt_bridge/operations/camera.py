from __future__ import annotations

from typing import Any

from ..protocol import BridgeError
from ..serialization import object_summary


def _bpy() -> Any:
    import bpy

    return bpy


def create_or_update_camera(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    obj = bpy.data.objects.get(args["camera_name"])
    created = False
    if obj is None:
        if not args.get("create_if_missing", True):
            raise BridgeError("CAMERA_NOT_FOUND", f"Camera not found: {args['camera_name']}", status=409)
        data = bpy.data.cameras.new(args["camera_name"])
        obj = bpy.data.objects.new(args["camera_name"], data)
        bpy.context.scene.collection.objects.link(obj)
        created = True
    if obj.type != "CAMERA":
        raise BridgeError("INVALID_OBJECT_TYPE", "Object is not a camera.", status=409)
    data = obj.data
    for field in ("location", "rotation_euler"):
        if field in args:
            setattr(obj, field, args[field])
    if "lens_mm" in args:
        data.lens = args["lens_mm"]
    if "sensor_width_mm" in args:
        data.sensor_width = args["sensor_width_mm"]
    if "clip_start" in args:
        data.clip_start = args["clip_start"]
    if "clip_end" in args:
        data.clip_end = args["clip_end"]
    data.type = "ORTHO" if args.get("camera_type") == "orthographic" else "PERSP"
    if "ortho_scale" in args:
        data.ortho_scale = args["ortho_scale"]
    if args.get("set_active", True):
        bpy.context.scene.camera = obj
    result = object_summary(obj)
    result["created"] = created
    result["active"] = bpy.context.scene.camera == obj
    return result

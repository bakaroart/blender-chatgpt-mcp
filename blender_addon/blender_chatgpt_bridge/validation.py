from __future__ import annotations

import math
import re
import uuid
from typing import Any

from .protocol import PROTOCOL_VERSION, BridgeError

MAX_NAME_LENGTH = 128
OPERATION_NAMES = {
    "get_status",
    "get_scene_summary",
    "get_object",
    "create_primitive",
    "duplicate_object",
    "rename_object",
    "set_transform",
    "set_visibility",
    "create_or_update_material",
    "assign_material",
    "create_light",
    "update_light",
    "create_or_update_camera",
    "set_world",
    "add_modifier",
    "remove_modifier",
    "delete_objects",
    "render_preview",
    "save_copy",
}

OBJECT_TYPES = {
    "mesh",
    "curve",
    "surface",
    "meta",
    "font",
    "armature",
    "lattice",
    "empty",
    "light",
    "camera",
    "speaker",
    "volume",
    "grease_pencil",
}
PRIMITIVE_TYPES = {"cube", "plane", "uv_sphere", "ico_sphere", "cylinder", "cone", "torus"}
LIGHT_TYPES = {"point", "sun", "spot", "area"}


def validate_request_envelope(payload: Any) -> tuple[str, str, dict[str, Any]]:
    if not isinstance(payload, dict):
        raise BridgeError("INVALID_REQUEST", "Request must be a JSON object.", status=400)
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or len(request_id) > 80:
        raise BridgeError("INVALID_REQUEST", "request_id must be a string.", status=400)
    try:
        uuid.UUID(request_id)
    except ValueError as exc:
        raise BridgeError("INVALID_REQUEST", "request_id must be a UUID.", status=400) from exc
    protocol_version = payload.get("protocol_version")
    if protocol_version is not None and not str(protocol_version).startswith(PROTOCOL_VERSION.split(".")[0] + "."):
        raise BridgeError("PROTOCOL_VERSION_MISMATCH", "Protocol major version is not supported.", status=400)
    operation = payload.get("operation")
    if operation not in OPERATION_NAMES:
        raise BridgeError("UNSUPPORTED_OPERATION", "Operation is not supported.", status=400)
    args = payload.get("args", {})
    if not isinstance(args, dict):
        raise BridgeError("INVALID_REQUEST", "args must be an object.", status=400)
    reject_bad_scalars(args)
    return request_id, operation, validate_operation_args(operation, args)


def reject_bad_scalars(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise BridgeError("VALIDATION_ERROR", "NaN and Infinity are not allowed.", status=400)
    if isinstance(value, str):
        if "\0" in value:
            raise BridgeError("VALIDATION_ERROR", "Strings must not contain null bytes.", status=400)
        if len(value) > 4096:
            raise BridgeError("VALIDATION_ERROR", "String value is too long.", status=400)
    if isinstance(value, list):
        for item in value:
            reject_bad_scalars(item)
    if isinstance(value, dict):
        for item in value.values():
            reject_bad_scalars(item)


def validate_operation_args(operation: str, args: dict[str, Any]) -> dict[str, Any]:
    validators = {
        "get_status": _empty,
        "get_scene_summary": _scene_summary,
        "get_object": _get_object,
        "create_primitive": _create_primitive,
        "duplicate_object": _duplicate_object,
        "rename_object": _rename_object,
        "set_transform": _set_transform,
        "set_visibility": _set_visibility,
        "create_or_update_material": _material,
        "assign_material": _assign_material,
        "create_light": _create_light,
        "update_light": _update_light,
        "create_or_update_camera": _camera,
        "set_world": _world,
        "add_modifier": _add_modifier,
        "remove_modifier": _remove_modifier,
        "delete_objects": _delete_objects,
        "render_preview": _render_preview,
        "save_copy": _save_copy,
    }
    return validators[operation](dict(args))


def _allowed(args: dict[str, Any], keys: set[str]) -> None:
    extra = set(args) - keys
    if extra:
        raise BridgeError("VALIDATION_ERROR", f"Unsupported field: {sorted(extra)[0]}", status=400)


def _name(value: Any, field: str = "name") -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_NAME_LENGTH or "\0" in value:
        raise BridgeError("VALIDATION_ERROR", f"{field} must be a non-empty string up to 128 characters.", status=400)
    return value


def _bool(value: Any, default: bool | None = None) -> bool:
    if value is None and default is not None:
        return default
    if not isinstance(value, bool):
        raise BridgeError("VALIDATION_ERROR", "Boolean field is invalid.", status=400)
    return value


def _number(value: Any, field: str, minimum: float, maximum: float, default: float | None = None) -> float:
    if value is None and default is not None:
        return default
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise BridgeError("VALIDATION_ERROR", f"{field} must be a finite number.", status=400)
    value = float(value)
    if value < minimum or value > maximum:
        raise BridgeError("VALIDATION_ERROR", f"{field} is outside the allowed range.", status=400)
    return value


def _int(value: Any, field: str, minimum: int, maximum: int, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum or value > maximum:
        raise BridgeError("VALIDATION_ERROR", f"{field} must be an integer in range.", status=400)
    return value


def _vec3(value: Any, field: str, default: list[float] | None = None) -> list[float]:
    if value is None and default is not None:
        return default
    if not isinstance(value, list) or len(value) != 3:
        raise BridgeError("VALIDATION_ERROR", f"{field} must contain exactly three numbers.", status=400)
    return [_number(component, field, -1_000_000, 1_000_000) for component in value]


def _color(value: Any, field: str, length: int, default: list[float] | None = None) -> list[float]:
    if value is None and default is not None:
        return default
    if not isinstance(value, list) or len(value) != length:
        raise BridgeError("VALIDATION_ERROR", f"{field} must contain {length} components.", status=400)
    return [_number(component, field, 0, 1) for component in value]


def _enum(value: Any, field: str, allowed: set[str], default: str | None = None) -> str:
    if value is None and default is not None:
        return default
    if value not in allowed:
        raise BridgeError("VALIDATION_ERROR", f"{field} has an unsupported value.", status=400)
    return str(value)


def _empty(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, set())
    return {}


def _scene_summary(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"include_hidden", "object_types", "max_objects"})
    object_types = args.get("object_types")
    if object_types is not None:
        if not isinstance(object_types, list) or any(item not in OBJECT_TYPES for item in object_types):
            raise BridgeError("VALIDATION_ERROR", "object_types contains an unsupported object type.", status=400)
    return {
        "include_hidden": _bool(args.get("include_hidden"), False),
        "object_types": object_types,
        "max_objects": _int(args.get("max_objects"), "max_objects", 1, 500, 100),
    }


def _get_object(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"name"})
    return {"name": _name(args.get("name"))}


def _create_primitive(args: dict[str, Any]) -> dict[str, Any]:
    base = {"primitive_type", "name", "location", "rotation_euler", "scale", "collection_name", "name_conflict"}
    per_type = {
        "cube": set(),
        "plane": {"radius"},
        "uv_sphere": {"segments", "ring_count", "radius"},
        "ico_sphere": {"segments", "radius"},
        "cylinder": {"vertices", "radius", "depth"},
        "cone": {"vertices", "radius", "depth"},
        "torus": {"major_radius", "minor_radius", "segments"},
    }
    primitive_type = _enum(args.get("primitive_type"), "primitive_type", PRIMITIVE_TYPES)
    _allowed(args, base | per_type[primitive_type])
    result = {
        "primitive_type": primitive_type,
        "name": _name(args.get("name")),
        "location": _vec3(args.get("location"), "location", [0, 0, 0]),
        "rotation_euler": _vec3(args.get("rotation_euler"), "rotation_euler", [0, 0, 0]),
        "scale": _vec3(args.get("scale"), "scale", [1, 1, 1]),
        "name_conflict": _enum(args.get("name_conflict"), "name_conflict", {"error", "unique"}, "error"),
    }
    if args.get("collection_name") is not None:
        result["collection_name"] = _name(args["collection_name"], "collection_name")
    for field in ("vertices", "segments", "ring_count"):
        if field in args:
            result[field] = _int(args[field], field, 3, 256)
    for field in ("radius", "major_radius", "minor_radius", "depth"):
        if field in args:
            result[field] = _number(args[field], field, 0.001, 10000)
    return result


def _duplicate_object(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"source_name", "new_name", "linked_data", "location", "rotation_euler", "scale"})
    result = {
        "source_name": _name(args.get("source_name"), "source_name"),
        "new_name": _name(args.get("new_name"), "new_name"),
        "linked_data": _bool(args.get("linked_data"), False),
    }
    for field in ("location", "rotation_euler", "scale"):
        if field in args:
            result[field] = _vec3(args[field], field)
    return result


def _rename_object(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"current_name", "new_name"})
    return {"current_name": _name(args.get("current_name"), "current_name"), "new_name": _name(args.get("new_name"), "new_name")}


def _set_transform(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"name", "location", "rotation_euler", "scale", "allow_zero_scale"})
    if not any(field in args for field in ("location", "rotation_euler", "scale")):
        raise BridgeError("VALIDATION_ERROR", "At least one transform field is required.", status=400)
    allow_zero = _bool(args.get("allow_zero_scale"), False)
    result: dict[str, Any] = {"name": _name(args.get("name")), "allow_zero_scale": allow_zero}
    for field in ("location", "rotation_euler", "scale"):
        if field in args:
            result[field] = _vec3(args[field], field)
    if "scale" in result and not allow_zero and any(component == 0 for component in result["scale"]):
        raise BridgeError("VALIDATION_ERROR", "Zero scale requires allow_zero_scale.", status=400)
    return result


def _set_visibility(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"name", "hide_viewport", "hide_render"})
    if "hide_viewport" not in args and "hide_render" not in args:
        raise BridgeError("VALIDATION_ERROR", "At least one visibility field is required.", status=400)
    result: dict[str, Any] = {"name": _name(args.get("name"))}
    if "hide_viewport" in args:
        result["hide_viewport"] = _bool(args["hide_viewport"])
    if "hide_render" in args:
        result["hide_render"] = _bool(args["hide_render"])
    return result


def _material(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"material_name", "create_if_missing", "base_color", "metallic", "roughness", "specular_ior_level", "transmission_weight", "alpha", "emission_color", "emission_strength", "blend_method"})
    result: dict[str, Any] = {"material_name": _name(args.get("material_name"), "material_name"), "create_if_missing": _bool(args.get("create_if_missing"), True)}
    if "base_color" in args:
        result["base_color"] = _color(args["base_color"], "base_color", 4)
    if "emission_color" in args:
        result["emission_color"] = _color(args["emission_color"], "emission_color", 3)
    for field in ("metallic", "roughness", "specular_ior_level", "transmission_weight", "alpha"):
        if field in args:
            result[field] = _number(args[field], field, 0, 1)
    if "emission_strength" in args:
        result["emission_strength"] = _number(args["emission_strength"], "emission_strength", 0, 1000)
    if "blend_method" in args:
        result["blend_method"] = _enum(args["blend_method"], "blend_method", {"opaque", "blend", "hashed", "clip"})
    return result


def _assign_material(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"object_name", "material_name", "slot_index", "replace_existing"})
    result = {"object_name": _name(args.get("object_name"), "object_name"), "material_name": _name(args.get("material_name"), "material_name"), "replace_existing": _bool(args.get("replace_existing"), False)}
    if "slot_index" in args:
        result["slot_index"] = _int(args["slot_index"], "slot_index", 0, 31)
    return result


def _create_light(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"name", "light_type", "location", "rotation_euler", "energy", "color", "size", "radius", "spot_size", "spot_blend"})
    result = {"name": _name(args.get("name")), "light_type": _enum(args.get("light_type"), "light_type", LIGHT_TYPES), "location": _vec3(args.get("location"), "location", [0, 0, 0]), "rotation_euler": _vec3(args.get("rotation_euler"), "rotation_euler", [0, 0, 0]), "energy": _number(args.get("energy"), "energy", 0, 1_000_000, 10), "color": _color(args.get("color"), "color", 3, [1, 1, 1])}
    for field in ("size", "radius"):
        if field in args:
            result[field] = _number(args[field], field, 0.001, 10000)
    for field in ("spot_size", "spot_blend"):
        if field in args:
            result[field] = _number(args[field], field, 0 if field == "spot_blend" else 0.001, 1 if field == "spot_blend" else math.pi)
    return result


def _update_light(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"name", "location", "rotation_euler", "energy", "color", "size", "radius", "spot_size", "spot_blend"})
    result: dict[str, Any] = {"name": _name(args.get("name"))}
    for field in ("location", "rotation_euler"):
        if field in args:
            result[field] = _vec3(args[field], field)
    if "energy" in args:
        result["energy"] = _number(args["energy"], "energy", 0, 1_000_000)
    if "color" in args:
        result["color"] = _color(args["color"], "color", 3)
    for field in ("size", "radius"):
        if field in args:
            result[field] = _number(args[field], field, 0.001, 10000)
    if "spot_size" in args:
        result["spot_size"] = _number(args["spot_size"], "spot_size", 0.001, math.pi)
    if "spot_blend" in args:
        result["spot_blend"] = _number(args["spot_blend"], "spot_blend", 0, 1)
    return result


def _camera(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"camera_name", "create_if_missing", "set_active", "location", "rotation_euler", "lens_mm", "sensor_width_mm", "clip_start", "clip_end", "camera_type", "ortho_scale"})
    result: dict[str, Any] = {"camera_name": _name(args.get("camera_name"), "camera_name"), "create_if_missing": _bool(args.get("create_if_missing"), True), "set_active": _bool(args.get("set_active"), True), "camera_type": _enum(args.get("camera_type"), "camera_type", {"perspective", "orthographic"}, "perspective")}
    for field in ("location", "rotation_euler"):
        if field in args:
            result[field] = _vec3(args[field], field)
    ranges = {"lens_mm": (1, 500), "sensor_width_mm": (1, 100), "clip_start": (0.001, 10000), "clip_end": (0.01, 1_000_000), "ortho_scale": (0.001, 100000)}
    for field, (minimum, maximum) in ranges.items():
        if field in args:
            result[field] = _number(args[field], field, minimum, maximum)
    if "clip_start" in result and "clip_end" in result and result["clip_start"] >= result["clip_end"]:
        raise BridgeError("VALIDATION_ERROR", "clip_start must be less than clip_end.", status=400)
    return result


def _world(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"color", "strength"})
    if "color" not in args and "strength" not in args:
        raise BridgeError("VALIDATION_ERROR", "At least one world field is required.", status=400)
    result: dict[str, Any] = {}
    if "color" in args:
        result["color"] = _color(args["color"], "color", 3)
    if "strength" in args:
        result["strength"] = _number(args["strength"], "strength", 0, 1000)
    return result


def _add_modifier(args: dict[str, Any]) -> dict[str, Any]:
    modifier_type = _enum(args.get("modifier_type"), "modifier_type", {"bevel", "subdivision_surface", "solidify", "mirror"})
    common = {"object_name", "modifier_type", "modifier_name"}
    allowed = {
        "bevel": {"width", "segments", "limit_method"},
        "subdivision_surface": {"levels_viewport", "levels_render", "subdivision_type"},
        "solidify": {"thickness", "offset"},
        "mirror": {"use_axis", "merge", "merge_threshold", "mirror_object_name"},
    }
    _allowed(args, common | allowed[modifier_type])
    result: dict[str, Any] = {"object_name": _name(args.get("object_name"), "object_name"), "modifier_type": modifier_type}
    if "modifier_name" in args:
        result["modifier_name"] = _name(args["modifier_name"], "modifier_name")
    if modifier_type == "bevel":
        result["width"] = _number(args.get("width"), "width", 0, 10000, 0.1)
        result["segments"] = _int(args.get("segments"), "segments", 1, 64, 1)
        result["limit_method"] = _enum(args.get("limit_method"), "limit_method", {"none", "angle", "weight"}, "none")
    elif modifier_type == "subdivision_surface":
        result["levels_viewport"] = _int(args.get("levels_viewport"), "levels_viewport", 0, 6, 1)
        result["levels_render"] = _int(args.get("levels_render"), "levels_render", 0, 6, 1)
        result["subdivision_type"] = _enum(args.get("subdivision_type"), "subdivision_type", {"catmull_clark", "simple"}, "catmull_clark")
    elif modifier_type == "solidify":
        result["thickness"] = _number(args.get("thickness"), "thickness", -10000, 10000, 0.1)
        result["offset"] = _number(args.get("offset"), "offset", -1, 1, 0)
    else:
        axis = args.get("use_axis", [True, False, False])
        if not isinstance(axis, list) or len(axis) != 3 or not all(isinstance(item, bool) for item in axis):
            raise BridgeError("VALIDATION_ERROR", "use_axis must contain exactly three booleans.", status=400)
        result["use_axis"] = axis
        result["merge"] = _bool(args.get("merge"), True)
        result["merge_threshold"] = _number(args.get("merge_threshold"), "merge_threshold", 0, 100, 0.001)
        if "mirror_object_name" in args:
            result["mirror_object_name"] = _name(args["mirror_object_name"], "mirror_object_name")
    return result


def _remove_modifier(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"object_name", "modifier_name"})
    return {"object_name": _name(args.get("object_name"), "object_name"), "modifier_name": _name(args.get("modifier_name"), "modifier_name")}


def _delete_objects(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"names"})
    names = args.get("names")
    if not isinstance(names, list) or not 1 <= len(names) <= 50:
        raise BridgeError("VALIDATION_ERROR", "names must contain one to fifty exact names.", status=400)
    if len(set(names)) != len(names):
        raise BridgeError("VALIDATION_ERROR", "Duplicate names are not allowed.", status=400)
    for name in names:
        _name(name)
        if re.search(r"[*?\[\]{}()|\\^$+]", name):
            raise BridgeError("VALIDATION_ERROR", "Wildcard, glob, and regex selectors are not allowed.", status=400)
    return {"names": names}


def _render_preview(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"width", "height", "samples", "format", "quality", "camera_name", "transparent_background"})
    width = _int(args.get("width"), "width", 64, 1024, 512)
    height = _int(args.get("height"), "height", 64, 1024, 512)
    if width * height > 1_048_576:
        raise BridgeError("VALIDATION_ERROR", "Preview pixel count is too high.", status=400)
    result = {"width": width, "height": height, "samples": _int(args.get("samples"), "samples", 1, 64, 16), "format": _enum(args.get("format"), "format", {"jpeg", "png"}, "jpeg"), "quality": _int(args.get("quality"), "quality", 30, 95, 85), "transparent_background": _bool(args.get("transparent_background"), False)}
    if "camera_name" in args:
        result["camera_name"] = _name(args["camera_name"], "camera_name")
    return result


def _save_copy(args: dict[str, Any]) -> dict[str, Any]:
    _allowed(args, {"relative_path", "compress", "create_directories"})
    path = args.get("relative_path")
    if not isinstance(path, str) or not path or "\0" in path or path.startswith("/") or ".." in re.split(r"[\\/]+", path) or not path.lower().endswith(".blend"):
        raise BridgeError("VALIDATION_ERROR", "relative_path must be a safe relative .blend path.", status=400)
    return {"relative_path": path, "compress": _bool(args.get("compress"), True), "create_directories": _bool(args.get("create_directories"), False)}

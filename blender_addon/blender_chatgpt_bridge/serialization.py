from __future__ import annotations

from typing import Any

from .protocol import MAX_MATERIAL_SLOTS


def vec(value: Any) -> list[float]:
    return [float(value[0]), float(value[1]), float(value[2])]


def color(value: Any, length: int = 4) -> list[float]:
    return [float(value[index]) for index in range(length)]


def object_summary(obj: Any, include_modifiers: bool = True) -> dict[str, Any]:
    data = getattr(obj, "data", None)
    summary: dict[str, Any] = {
        "name": obj.name,
        "type": str(obj.type).lower(),
        "location": vec(obj.location),
        "rotation_euler": vec(obj.rotation_euler),
        "scale": vec(obj.scale),
        "dimensions": vec(obj.dimensions),
        "visible": bool(obj.visible_get()),
        "selected": bool(obj.select_get()),
        "parent": obj.parent.name if obj.parent else None,
        "collections": [collection.name for collection in obj.users_collection],
        "materials": [
            slot.material.name if slot.material else None for slot in list(obj.material_slots)[:MAX_MATERIAL_SLOTS]
        ],
    }
    if data is not None and obj.type == "MESH":
        summary["mesh_counts"] = {
            "vertices": len(data.vertices),
            "edges": len(data.edges),
            "polygons": len(data.polygons),
        }
    if obj.type == "CAMERA" and data is not None:
        summary["camera"] = {
            "type": str(data.type).lower(),
            "lens_mm": float(data.lens),
            "sensor_width_mm": float(data.sensor_width),
            "clip_start": float(data.clip_start),
            "clip_end": float(data.clip_end),
            "ortho_scale": float(data.ortho_scale),
        }
    if obj.type == "LIGHT" and data is not None:
        summary["light"] = {
            "type": str(data.type).lower(),
            "energy": float(data.energy),
            "color": color(data.color, 3),
        }
        if hasattr(data, "size"):
            summary["light"]["size"] = float(data.size)
        if hasattr(data, "spot_size"):
            summary["light"]["spot_size"] = float(data.spot_size)
            summary["light"]["spot_blend"] = float(data.spot_blend)
    if include_modifiers:
        summary["modifiers"] = [modifier_summary(modifier) for modifier in obj.modifiers]
    return summary


def modifier_summary(modifier: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"name": modifier.name, "type": str(modifier.type).lower()}
    for field in (
        "width",
        "segments",
        "limit_method",
        "levels",
        "render_levels",
        "subdivision_type",
        "thickness",
        "offset",
        "use_axis",
        "use_clip",
        "use_mirror_merge",
        "merge_threshold",
    ):
        if hasattr(modifier, field):
            value = getattr(modifier, field)
            if isinstance(value, (list, tuple)):
                result[field] = list(value)
            else:
                result[field] = value
    if hasattr(modifier, "mirror_object") and modifier.mirror_object:
        result["mirror_object_name"] = modifier.mirror_object.name
    return result


def material_slots(obj: Any) -> list[str | None]:
    return [slot.material.name if slot.material else None for slot in list(obj.material_slots)[:MAX_MATERIAL_SLOTS]]

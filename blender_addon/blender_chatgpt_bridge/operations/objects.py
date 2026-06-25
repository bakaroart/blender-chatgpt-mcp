from __future__ import annotations

from typing import Any

from ..protocol import BridgeError
from ..serialization import material_slots, modifier_summary, object_summary


def _bpy() -> Any:
    import bpy

    return bpy


def _get_object(name: str) -> Any:
    bpy = _bpy()
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise BridgeError("OBJECT_NOT_FOUND", f"Object not found: {name}", status=409)
    return obj


def _ensure_no_object(name: str) -> None:
    bpy = _bpy()
    if bpy.data.objects.get(name) is not None:
        raise BridgeError("OBJECT_NAME_CONFLICT", f"Object already exists: {name}", status=409)


def _unique_name(base: str) -> str:
    bpy = _bpy()
    if bpy.data.objects.get(base) is None:
        return base
    for index in range(1, 1000):
        candidate = f"{base}.{index:03d}"
        if bpy.data.objects.get(candidate) is None:
            return candidate
    raise BridgeError("OBJECT_NAME_CONFLICT", "Unable to create a unique object name.", status=409)


def _collection(name: str | None) -> Any:
    bpy = _bpy()
    if not name:
        return bpy.context.scene.collection
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def get_object(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    return object_summary(_get_object(args["name"]))


def create_primitive(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    name = args["name"] if args.get("name_conflict", "error") == "error" else _unique_name(args["name"])
    if args.get("name_conflict", "error") == "error":
        _ensure_no_object(name)
    collection = _collection(args.get("collection_name"))
    primitive_type = args["primitive_type"]
    common = {"location": args["location"], "rotation": args["rotation_euler"]}
    if primitive_type == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2, **common)
    elif primitive_type == "plane":
        bpy.ops.mesh.primitive_plane_add(size=float(args.get("radius", 1.0)), **common)
    elif primitive_type == "uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=int(args.get("segments", 32)),
            ring_count=int(args.get("ring_count", 16)),
            radius=float(args.get("radius", 1.0)),
            **common,
        )
    elif primitive_type == "ico_sphere":
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=int(args.get("segments", 2)), radius=float(args.get("radius", 1.0)), **common)
    elif primitive_type == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=int(args.get("vertices", 32)), radius=float(args.get("radius", 1.0)), depth=float(args.get("depth", 2.0)), **common)
    elif primitive_type == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=int(args.get("vertices", 32)), radius1=float(args.get("radius", 1.0)), depth=float(args.get("depth", 2.0)), **common)
    elif primitive_type == "torus":
        bpy.ops.mesh.primitive_torus_add(major_segments=int(args.get("segments", 48)), major_radius=float(args.get("major_radius", 1.0)), minor_radius=float(args.get("minor_radius", 0.25)), **common)
    else:
        raise BridgeError("VALIDATION_ERROR", "Unsupported primitive type.", status=400)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}Mesh"
    obj.scale = args["scale"]
    if collection.name not in {item.name for item in obj.users_collection}:
        collection.objects.link(obj)
    for existing in list(obj.users_collection):
        if existing != collection and existing.name == bpy.context.scene.collection.name:
            existing.objects.unlink(obj)
    return object_summary(obj)


def duplicate_object(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    _ensure_no_object(args["new_name"])
    source = _get_object(args["source_name"])
    copy = source.copy()
    copy.name = args["new_name"]
    if source.data and not args.get("linked_data", False):
        copy.data = source.data.copy()
        copy.data.name = f"{args['new_name']}Data"
    for field in ("location", "rotation_euler", "scale"):
        if field in args:
            setattr(copy, field, args[field])
    collections = list(source.users_collection) or [_bpy().context.scene.collection]
    for collection in collections:
        collection.objects.link(copy)
    return object_summary(copy)


def rename_object(args: dict[str, Any], _context: Any) -> dict[str, str]:
    obj = _get_object(args["current_name"])
    _ensure_no_object(args["new_name"])
    old_name = obj.name
    obj.name = args["new_name"]
    return {"old_name": old_name, "new_name": obj.name}


def set_transform(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _get_object(args["name"])
    for field in ("location", "rotation_euler", "scale"):
        if field in args:
            setattr(obj, field, args[field])
    return {
        "name": obj.name,
        "location": list(obj.location),
        "rotation_euler": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def set_visibility(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _get_object(args["name"])
    if "hide_viewport" in args:
        obj.hide_viewport = bool(args["hide_viewport"])
    if "hide_render" in args:
        obj.hide_render = bool(args["hide_render"])
    return {"name": obj.name, "hide_viewport": bool(obj.hide_viewport), "hide_render": bool(obj.hide_render)}


def add_modifier(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _get_object(args["object_name"])
    modifier_type = args["modifier_type"]
    blender_types = {
        "bevel": "BEVEL",
        "subdivision_surface": "SUBSURF",
        "solidify": "SOLIDIFY",
        "mirror": "MIRROR",
    }
    modifier_name = args.get("modifier_name") or modifier_type
    modifier = obj.modifiers.new(modifier_name, blender_types[modifier_type])
    if modifier_type == "bevel":
        modifier.width = args["width"]
        modifier.segments = args["segments"]
        modifier.limit_method = args["limit_method"].upper()
    elif modifier_type == "subdivision_surface":
        modifier.levels = args["levels_viewport"]
        modifier.render_levels = args["levels_render"]
        modifier.subdivision_type = "CATMULL_CLARK" if args["subdivision_type"] == "catmull_clark" else "SIMPLE"
    elif modifier_type == "solidify":
        modifier.thickness = args["thickness"]
        modifier.offset = args["offset"]
    elif modifier_type == "mirror":
        modifier.use_axis = args["use_axis"]
        modifier.use_mirror_merge = args["merge"]
        modifier.merge_threshold = args["merge_threshold"]
        if args.get("mirror_object_name"):
            modifier.mirror_object = _get_object(args["mirror_object_name"])
    return modifier_summary(modifier)


def remove_modifier(args: dict[str, Any], _context: Any) -> dict[str, str]:
    bpy = _bpy()
    obj = _get_object(args["object_name"])
    modifier = obj.modifiers.get(args["modifier_name"])
    if modifier is None:
        raise BridgeError("VALIDATION_ERROR", "Modifier not found.", status=409)
    try:
        bpy.ops.ed.undo_push(message="Remove modifier via MCP bridge")
    except Exception:
        pass
    removed_name = modifier.name
    obj.modifiers.remove(modifier)
    return {"object_name": obj.name, "removed_modifier_name": removed_name}


def delete_objects(args: dict[str, Any], _context: Any) -> dict[str, list[str]]:
    bpy = _bpy()
    names = args["names"]
    objects = []
    for name in names:
        objects.append(_get_object(name))
    try:
        bpy.ops.ed.undo_push(message="Delete objects via MCP bridge")
    except Exception:
        pass
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    return {"deleted_names": names}


def slots_for_object(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _get_object(args["object_name"])
    return {"object_name": obj.name, "material_slots": material_slots(obj)}

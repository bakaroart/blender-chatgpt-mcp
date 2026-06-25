from __future__ import annotations

from typing import Any

from ..protocol import BridgeError
from ..serialization import material_slots


def _bpy() -> Any:
    import bpy

    return bpy


def _object(name: str) -> Any:
    obj = _bpy().data.objects.get(name)
    if obj is None:
        raise BridgeError("OBJECT_NOT_FOUND", f"Object not found: {name}", status=409)
    return obj


def _material(name: str) -> Any:
    material = _bpy().data.materials.get(name)
    if material is None:
        raise BridgeError("MATERIAL_NOT_FOUND", f"Material not found: {name}", status=409)
    return material


def _set_socket(bsdf: Any, socket_name: str, value: Any) -> None:
    socket = bsdf.inputs.get(socket_name)
    if socket is not None:
        socket.default_value = value


def create_or_update_material(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    material = bpy.data.materials.get(args["material_name"])
    if material is None:
        if not args.get("create_if_missing", True):
            raise BridgeError("MATERIAL_NOT_FOUND", f"Material not found: {args['material_name']}", status=409)
        material = bpy.data.materials.new(args["material_name"])
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if bsdf is not None:
        if "base_color" in args:
            _set_socket(bsdf, "Base Color", args["base_color"])
        for field, socket_name in (
            ("metallic", "Metallic"),
            ("roughness", "Roughness"),
            ("specular_ior_level", "Specular IOR Level"),
            ("transmission_weight", "Transmission Weight"),
            ("alpha", "Alpha"),
            ("emission_color", "Emission Color"),
            ("emission_strength", "Emission Strength"),
        ):
            if field in args:
                _set_socket(bsdf, socket_name, args[field])
    if "blend_method" in args and hasattr(material, "blend_method"):
        material.blend_method = args["blend_method"].upper()
    if "alpha" in args:
        material.diffuse_color[3] = args["alpha"]
    if "base_color" in args:
        material.diffuse_color = args["base_color"]
    return {
        "material_name": material.name,
        "base_color": list(material.diffuse_color),
        "blend_method": getattr(material, "blend_method", None),
        "use_nodes": bool(material.use_nodes),
    }


def assign_material(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    obj = _object(args["object_name"])
    if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT", "META"}:
        raise BridgeError("INVALID_OBJECT_TYPE", "Object does not support material slots.", status=409)
    material = _material(args["material_name"])
    slot_index = args.get("slot_index")
    replace_existing = args.get("replace_existing", False)
    if slot_index is None:
        if replace_existing and obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    else:
        while len(obj.data.materials) <= slot_index:
            obj.data.materials.append(None)
        if obj.data.materials[slot_index] is not None and not replace_existing:
            raise BridgeError("VALIDATION_ERROR", "Material slot is occupied and replace_existing is false.", status=409)
        obj.data.materials[slot_index] = material
    return {"object_name": obj.name, "material_slots": material_slots(obj)}

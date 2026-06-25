from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .protocol import BridgeError
from .validation import validate_operation_args
from .operations import camera, files, lights, materials, objects, render, scene, status


@dataclass
class BridgeContext:
    project_root: str | None = None
    temp_dir: str | None = None
    normal_timeout: float = 30.0
    render_timeout: float = 120.0


OperationHandler = Callable[[dict[str, Any], BridgeContext], Any]

OPERATIONS: dict[str, tuple[OperationHandler, bool]] = {
    "get_status": (status.get_status, False),
    "get_scene_summary": (status.get_scene_summary, False),
    "get_object": (objects.get_object, False),
    "create_primitive": (objects.create_primitive, True),
    "duplicate_object": (objects.duplicate_object, True),
    "rename_object": (objects.rename_object, True),
    "set_transform": (objects.set_transform, True),
    "set_visibility": (objects.set_visibility, True),
    "create_or_update_material": (materials.create_or_update_material, True),
    "assign_material": (materials.assign_material, True),
    "create_light": (lights.create_light, True),
    "update_light": (lights.update_light, True),
    "create_or_update_camera": (camera.create_or_update_camera, True),
    "set_world": (scene.set_world, True),
    "add_modifier": (objects.add_modifier, True),
    "remove_modifier": (objects.remove_modifier, True),
    "delete_objects": (objects.delete_objects, True),
    "render_preview": (render.render_preview, False),
    "save_copy": (files.save_copy, True),
}


def is_mutating(operation: str) -> bool:
    entry = OPERATIONS.get(operation)
    if not entry:
        raise BridgeError("UNSUPPORTED_OPERATION", "Operation is not supported.", status=400)
    return entry[1]


def dispatch(operation: str, args: dict[str, Any], context: BridgeContext) -> Any:
    entry = OPERATIONS.get(operation)
    if not entry:
        raise BridgeError("UNSUPPORTED_OPERATION", "Operation is not supported.", status=400)
    validated = validate_operation_args(operation, args)
    return entry[0](validated, context)

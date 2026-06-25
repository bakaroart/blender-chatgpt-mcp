from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ADDON_PARENT = ROOT / "blender_addon"
sys.path.insert(0, str(ADDON_PARENT))

from blender_chatgpt_bridge.dispatcher import BridgeContext, dispatch


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> None:
    context = BridgeContext(project_root=str(ROOT), temp_dir=str(ROOT / "dist" / "preview-tests"))
    dispatch(
        "create_primitive",
        {
            "primitive_type": "cube",
            "name": "MCPSmokeCube",
            "location": [0, 0, 0],
            "rotation_euler": [0, 0, 0],
            "scale": [1, 1, 1],
            "name_conflict": "error",
        },
        context,
    )
    dispatch("set_transform", {"name": "MCPSmokeCube", "location": [1, 2, 3]}, context)
    dispatch(
        "create_or_update_material",
        {
            "material_name": "MCPSmokeMaterial",
            "base_color": [0.2, 0.4, 0.8, 1.0],
            "roughness": 0.5,
        },
        context,
    )
    dispatch(
        "assign_material",
        {
            "object_name": "MCPSmokeCube",
            "material_name": "MCPSmokeMaterial",
            "replace_existing": True,
        },
        context,
    )
    dispatch(
        "create_or_update_camera",
        {
            "camera_name": "MCPSmokeCamera",
            "location": [4, -6, 4],
            "rotation_euler": [1.1, 0, 0.6],
            "set_active": True,
        },
        context,
    )
    dispatch(
        "create_light",
        {
            "name": "MCPSmokeLight",
            "light_type": "area",
            "location": [2, -3, 4],
            "energy": 200,
            "color": [1, 1, 1],
        },
        context,
    )
    summary = dispatch("get_scene_summary", {"max_objects": 10}, context)
    assert_true(any(obj["name"] == "MCPSmokeCube" for obj in summary["objects"]), "cube missing")
    if not (os.environ.get("BLENDER_MCP_SKIP_RENDER") or os.environ.get("BLENDER_CHATGPT_SKIP_RENDER")):
        preview = dispatch("render_preview", {"width": 64, "height": 64, "samples": 1, "format": "jpeg"}, context)
        assert_true(preview["byte_size"] > 0, "preview is empty")
    dispatch("delete_objects", {"names": ["MCPSmokeCube", "MCPSmokeCamera", "MCPSmokeLight"]}, context)
    material = bpy.data.materials.get("MCPSmokeMaterial")
    if material:
        bpy.data.materials.remove(material)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
    sys.exit(0)

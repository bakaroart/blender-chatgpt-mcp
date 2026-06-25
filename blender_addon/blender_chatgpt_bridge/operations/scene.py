from __future__ import annotations

from typing import Any


def _bpy() -> Any:
    import bpy

    return bpy


def set_world(args: dict[str, Any], _context: Any) -> dict[str, Any]:
    bpy = _bpy()
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    world = scene.world
    if "color" in args:
        world.color = args["color"]
    world.use_nodes = True
    strength = args.get("strength")
    if world.node_tree:
        background = world.node_tree.nodes.get("Background")
        if background:
            if "color" in args and background.inputs.get("Color"):
                background.inputs["Color"].default_value = [*args["color"], 1.0]
            if strength is not None and background.inputs.get("Strength"):
                background.inputs["Strength"].default_value = strength
    return {
        "world_name": world.name,
        "color": list(world.color),
        "strength": strength,
    }

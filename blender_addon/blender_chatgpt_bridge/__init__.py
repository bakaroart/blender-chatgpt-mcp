from __future__ import annotations

bl_info = {
    "name": "Blender MCP Bridge",
    "author": "blender-chatgpt-mcp contributors",
    "version": (0, 1, 0),
    "blender": (5, 1, 0),
    "location": "3D View > Sidebar > MCP Bridge",
    "description": "Authenticated localhost bridge for MCP tools",
    "category": "3D View",
}

try:
    import bpy
    from bpy.app.handlers import persistent
except ModuleNotFoundError:
    bpy = None

    def persistent(function):
        return function


def _auto_start() -> None:
    from . import bridge_server
    from .preferences import get_preferences

    prefs = get_preferences()
    if prefs.auto_start and prefs.bridge_token:
        bridge_server.start_bridge(
            prefs.port,
            prefs.bridge_token,
            prefs.project_root or None,
            prefs.normal_timeout,
            prefs.render_timeout,
            prefs.audit_log_path or None,
        )
    return None


@persistent
def _exit_pre(_dummy: object) -> None:
    from . import bridge_server

    bridge_server.stop_bridge()


def register() -> None:
    if bpy is None:
        raise RuntimeError("This add-on can only be registered inside Blender.")
    from .operators import (
        BLENDER_CHATGPT_OT_copy_token,
        BLENDER_CHATGPT_OT_generate_token,
        BLENDER_CHATGPT_OT_start_bridge,
        BLENDER_CHATGPT_OT_stop_bridge,
    )
    from .panel import BLENDER_CHATGPT_PT_bridge
    from .preferences import BlenderChatGPTBridgePreferences

    classes = (
        BlenderChatGPTBridgePreferences,
        BLENDER_CHATGPT_OT_start_bridge,
        BLENDER_CHATGPT_OT_stop_bridge,
        BLENDER_CHATGPT_OT_generate_token,
        BLENDER_CHATGPT_OT_copy_token,
        BLENDER_CHATGPT_PT_bridge,
    )
    for cls in classes:
        bpy.utils.register_class(cls)
    if _exit_pre not in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.append(_exit_pre)
    bpy.app.timers.register(_auto_start, first_interval=1.0)


def unregister() -> None:
    if bpy is None:
        return
    from . import bridge_server
    from .operators import (
        BLENDER_CHATGPT_OT_copy_token,
        BLENDER_CHATGPT_OT_generate_token,
        BLENDER_CHATGPT_OT_start_bridge,
        BLENDER_CHATGPT_OT_stop_bridge,
    )
    from .panel import BLENDER_CHATGPT_PT_bridge
    from .preferences import BlenderChatGPTBridgePreferences

    classes = (
        BlenderChatGPTBridgePreferences,
        BLENDER_CHATGPT_OT_start_bridge,
        BLENDER_CHATGPT_OT_stop_bridge,
        BLENDER_CHATGPT_OT_generate_token,
        BLENDER_CHATGPT_OT_copy_token,
        BLENDER_CHATGPT_PT_bridge,
    )
    bridge_server.stop_bridge()
    if _exit_pre in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.remove(_exit_pre)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

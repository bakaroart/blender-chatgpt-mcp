from __future__ import annotations

import bpy

from . import bridge_server
from .preferences import get_preferences
from .security import generate_token


class BLENDER_CHATGPT_OT_start_bridge(bpy.types.Operator):
    bl_idname = "blender_chatgpt_bridge.start"
    bl_label = "Start MCP Bridge"
    bl_description = "Start the authenticated localhost MCP bridge"

    def execute(self, context: bpy.types.Context) -> set[str]:
        prefs = get_preferences(context)
        try:
            bridge_server.start_bridge(
                prefs.port,
                prefs.bridge_token,
                prefs.project_root or None,
                prefs.normal_timeout,
                prefs.render_timeout,
                prefs.audit_log_path or None,
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Bridge start failed: {type(exc).__name__}")
            return {"CANCELLED"}
        self.report({"INFO"}, "MCP bridge started on 127.0.0.1")
        return {"FINISHED"}


class BLENDER_CHATGPT_OT_stop_bridge(bpy.types.Operator):
    bl_idname = "blender_chatgpt_bridge.stop"
    bl_label = "Stop MCP Bridge"
    bl_description = "Stop the MCP bridge"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        bridge_server.stop_bridge()
        self.report({"INFO"}, "MCP bridge stopped")
        return {"FINISHED"}


class BLENDER_CHATGPT_OT_generate_token(bpy.types.Operator):
    bl_idname = "blender_chatgpt_bridge.generate_token"
    bl_label = "Generate Token"
    bl_description = "Generate a high-entropy bridge bearer token"

    def execute(self, context: bpy.types.Context) -> set[str]:
        prefs = get_preferences(context)
        prefs.bridge_token = generate_token()
        self.report({"INFO"}, "Bridge token generated")
        return {"FINISHED"}


class BLENDER_CHATGPT_OT_copy_token(bpy.types.Operator):
    bl_idname = "blender_chatgpt_bridge.copy_token"
    bl_label = "Copy Token"
    bl_description = "Copy the configured token to Blender's clipboard"

    def execute(self, context: bpy.types.Context) -> set[str]:
        prefs = get_preferences(context)
        if not prefs.bridge_token:
            self.report({"ERROR"}, "No bridge token configured")
            return {"CANCELLED"}
        context.window_manager.clipboard = prefs.bridge_token
        self.report({"INFO"}, "Bridge token copied")
        return {"FINISHED"}

from __future__ import annotations

import bpy

from . import bridge_server
from .preferences import get_preferences


class BLENDER_CHATGPT_PT_bridge(bpy.types.Panel):
    bl_label = "MCP Bridge"
    bl_idname = "BLENDER_CHATGPT_PT_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MCP Bridge"

    def draw(self, context: bpy.types.Context) -> None:
        prefs = get_preferences(context)
        status = bridge_server.get_status()
        layout = self.layout
        layout.label(text=f"Status: {status.get('status', 'stopped')}")
        layout.label(text="Bind: 127.0.0.1")
        layout.label(text=f"Port: {prefs.port}")
        layout.label(text=f"Project Root: {prefs.project_root or 'Not set'}")
        layout.label(text=f"Token: {'Configured' if prefs.bridge_token else 'Missing'}")
        layout.label(text=f"File: {bpy.data.filepath or 'Unsaved'}")
        layout.label(text=f"Queue Depth: {status.get('queue_depth', 0)}")
        if status.get("last_error"):
            layout.label(text=f"Last Error: {status['last_error']}", icon="ERROR")
        row = layout.row(align=True)
        row.operator("blender_chatgpt_bridge.start", icon="PLAY")
        row.operator("blender_chatgpt_bridge.stop", icon="PAUSE")
        row = layout.row(align=True)
        row.operator("blender_chatgpt_bridge.generate_token", icon="KEY_HLT")
        row.operator("blender_chatgpt_bridge.copy_token", icon="COPYDOWN")

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty

ADDON_ID = "blender_chatgpt_bridge"


def get_preferences(context: bpy.types.Context | None = None) -> "BlenderChatGPTBridgePreferences":
    context = context or bpy.context
    return context.preferences.addons[ADDON_ID].preferences


class BlenderChatGPTBridgePreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    port: IntProperty(name="Port", default=8765, min=1, max=65535)
    project_root: StringProperty(name="Project Root", subtype="DIR_PATH", default="")
    bridge_token: StringProperty(name="Bridge Token", subtype="PASSWORD", default="")
    auto_start: BoolProperty(name="Auto Start", default=False)
    normal_timeout: FloatProperty(name="Normal Command Timeout", default=30.0, min=1.0, max=300.0)
    render_timeout: FloatProperty(name="Render Timeout", default=120.0, min=5.0, max=600.0)
    audit_log_path: StringProperty(name="Audit Log Path", default="")

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "port")
        layout.prop(self, "project_root")
        layout.prop(self, "bridge_token")
        row = layout.row(align=True)
        row.operator("blender_chatgpt_bridge.generate_token", icon="KEY_HLT")
        row.operator("blender_chatgpt_bridge.copy_token", icon="COPYDOWN")
        layout.prop(self, "auto_start")
        layout.prop(self, "normal_timeout")
        layout.prop(self, "render_timeout")
        layout.prop(self, "audit_log_path")

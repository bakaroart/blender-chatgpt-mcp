# Tool Reference

Every tool returns `structuredContent` with `ok`, `result` or `error`, and `warnings` when available. Every tool has `openWorldHint: false`.

| Tool | Access | Parameters |
| --- | --- | --- |
| `blender_get_status` | read-only | none |
| `blender_get_scene_summary` | read-only | `include_hidden`, `object_types`, `max_objects` up to 500 |
| `blender_get_object` | read-only | exact `name` |
| `blender_create_primitive` | write | `primitive_type`, `name`, transform, optional collection, fixed primitive settings |
| `blender_duplicate_object` | write | `source_name`, `new_name`, `linked_data`, optional transform |
| `blender_rename_object` | write | `current_name`, `new_name` |
| `blender_set_transform` | write | exact `name`, at least one of location/rotation/scale |
| `blender_set_visibility` | write | exact `name`, `hide_viewport` and/or `hide_render` |
| `blender_create_or_update_material` | write | Principled BSDF material fields only |
| `blender_assign_material` | write | `object_name`, existing `material_name`, optional slot |
| `blender_create_light` | write | point/sun/spot/area with bounded settings |
| `blender_update_light` | write | exact light object and typed settings |
| `blender_create_or_update_camera` | write | camera name, type, transform, optics, clipping |
| `blender_set_world` | write | background color and/or strength |
| `blender_add_modifier` | write | bevel, subdivision surface, solidify, or mirror |
| `blender_remove_modifier` | destructive | exact object and modifier name |
| `blender_delete_objects` | destructive | 1-50 exact names; no wildcards |
| `blender_render_preview` | read-only | 64-1024 width/height, max 1,048,576 pixels, max 64 samples |
| `blender_save_copy` | write | relative `.blend` path under project root, no overwrite |

Destructive tools use `destructiveHint: true`. Bounded writes use `readOnlyHint: false`, `destructiveHint: false`. Preview returns an MCP image content block plus metadata.

## Defaults And Limits

- Names: maximum 128 characters, exact match required.
- Scene summary: `include_hidden=false`, `max_objects=100`, maximum 500.
- Material slots returned: maximum 32.
- Preview: `width=512`, `height=512`, `samples=16`, `format=jpeg`, `quality=85`; dimensions 64-1024, maximum 1,048,576 pixels, maximum 64 samples, target encoded payload under 2 MB.
- Delete: 1-50 explicit names; duplicates, wildcards, globs, regex syntax, and empty lists are rejected.
- Save copy: relative `.blend` path only, no overwrite, `compress=true`, `create_directories=false`.

## Side Effects

- Read-only tools do not persist scene changes. `blender_render_preview` temporarily changes render settings and restores them in `finally`.
- Write tools mutate the active Blender scene but do not write files unless the tool is `blender_save_copy`.
- `blender_remove_modifier` and `blender_delete_objects` push undo checkpoints where Blender supports it.
- No tool publishes outside the local Blender process or configured project root.

## Examples

Get a scene summary:

```json
{"include_hidden": false, "max_objects": 50}
```

Create a cube:

```json
{"primitive_type":"cube","name":"Demo Cube","location":[0,0,1],"scale":[1,1,1]}
```

Assign a material:

```json
{"object_name":"Demo Cube","material_name":"Blue Paint","replace_existing":true}
```

Render a preview:

```json
{"width":512,"height":512,"samples":16,"format":"jpeg","quality":85}
```

Save a copy:

```json
{"relative_path":"exports/scene-copy.blend","create_directories":true}
```

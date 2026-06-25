import { Buffer } from "node:buffer";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { CallToolResultSchema, ListToolsResultSchema } from "@modelcontextprotocol/sdk/types.js";

const serverUrl = process.env.MCP_URL ?? "http://127.0.0.1:3000/mcp";
const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
const previewPath = join(process.cwd(), "dist", "showcase-preview.jpg");
const blendRelativePath = `dist/showcase-${timestamp}.blend`;

type ToolResult = {
  content?: Array<{ type: string; text?: string; data?: string; mimeType?: string }>;
  structuredContent?: unknown;
};

const client = new Client({
  name: "blender-chatgpt-showcase",
  version: "0.1.0"
});

const callTool = async (name: string, args: Record<string, unknown>): Promise<ToolResult> => {
  const result = await client.request(
    {
      method: "tools/call",
      params: {
        name,
        arguments: args
      }
    },
    CallToolResultSchema
  );
  const firstText = result.content.find((item) => item.type === "text")?.text;
  console.log(`${name}: ${firstText ?? "ok"}`);
  return result as ToolResult;
};

const objectNames = (result: ToolResult): string[] => {
  const structured = result.structuredContent as { result?: { objects?: Array<{ name?: unknown }> } } | undefined;
  return (
    structured?.result?.objects
      ?.map((object) => object.name)
      .filter((name): name is string => typeof name === "string") ?? []
  );
};

const main = async (): Promise<void> => {
  const transport = new StreamableHTTPClientTransport(new URL(serverUrl));
  await client.connect(transport as unknown as Transport);

  const tools = await client.request({ method: "tools/list", params: {} }, ListToolsResultSchema);
  console.log(`connected: ${tools.tools.length} tools available`);

  const before = await callTool("blender_get_scene_summary", { include_hidden: true, max_objects: 200 });
  const staleNames = objectNames(before).filter((name) => name.startsWith("CodexShowcase") || name.startsWith("CodexLive"));
  if (staleNames.length > 0) {
    await callTool("blender_delete_objects", { names: staleNames });
  }

  await callTool("blender_create_primitive", {
    primitive_type: "plane",
    name: "CodexShowcaseFloor",
    radius: 7,
    location: [0, 0, 0],
    rotation_euler: [0, 0, 0],
    scale: [1, 1, 1]
  });
  await callTool("blender_create_primitive", {
    primitive_type: "cube",
    name: "CodexShowcasePedestal",
    location: [0, 0, 0.25],
    rotation_euler: [0, 0, 0.78],
    scale: [1.6, 1.6, 0.25]
  });
  await callTool("blender_add_modifier", {
    object_name: "CodexShowcasePedestal",
    modifier_type: "bevel",
    modifier_name: "softened_edges",
    width: 0.08,
    segments: 8,
    limit_method: "none"
  });
  await callTool("blender_create_primitive", {
    primitive_type: "uv_sphere",
    name: "CodexShowcaseOrb",
    location: [0, 0, 1.55],
    rotation_euler: [0, 0, 0],
    scale: [0.9, 0.9, 0.9],
    segments: 48,
    ring_count: 24,
    radius: 1
  });
  await callTool("blender_add_modifier", {
    object_name: "CodexShowcaseOrb",
    modifier_type: "subdivision_surface",
    modifier_name: "polish",
    levels_viewport: 1,
    levels_render: 1,
    subdivision_type: "catmull_clark"
  });
  await callTool("blender_create_primitive", {
    primitive_type: "torus",
    name: "CodexShowcaseRing",
    location: [0, 0, 1.55],
    rotation_euler: [0.85, 0.18, 0.35],
    scale: [1, 1, 1],
    major_radius: 1.25,
    minor_radius: 0.06,
    segments: 96
  });

  const materials = [
    ["CodexShowcaseFloorMat", [0.025, 0.03, 0.04, 1], 0.0, 0.65],
    ["CodexShowcasePedestalMat", [0.18, 0.19, 0.2, 1], 0.25, 0.38],
    ["CodexShowcaseOrbMat", [0.05, 0.32, 0.95, 1], 0.0, 0.22],
    ["CodexShowcaseRingMat", [0.0, 0.95, 0.82, 1], 0.6, 0.18]
  ] as const;
  for (const [materialName, baseColor, metallic, roughness] of materials) {
    await callTool("blender_create_or_update_material", {
      material_name: materialName,
      base_color: baseColor,
      metallic,
      roughness
    });
  }

  await callTool("blender_assign_material", {
    object_name: "CodexShowcaseFloor",
    material_name: "CodexShowcaseFloorMat",
    replace_existing: true
  });
  await callTool("blender_assign_material", {
    object_name: "CodexShowcasePedestal",
    material_name: "CodexShowcasePedestalMat",
    replace_existing: true
  });
  await callTool("blender_assign_material", {
    object_name: "CodexShowcaseOrb",
    material_name: "CodexShowcaseOrbMat",
    replace_existing: true
  });
  await callTool("blender_assign_material", {
    object_name: "CodexShowcaseRing",
    material_name: "CodexShowcaseRingMat",
    replace_existing: true
  });

  await callTool("blender_create_light", {
    name: "CodexShowcaseKeyLight",
    light_type: "area",
    location: [3.5, -4.5, 5.5],
    energy: 650,
    color: [1, 0.93, 0.84],
    size: 4.5
  });
  await callTool("blender_create_light", {
    name: "CodexShowcaseRimLight",
    light_type: "point",
    location: [-3.5, 3.2, 3.4],
    energy: 120,
    color: [0.35, 0.8, 1],
    radius: 2.2
  });
  await callTool("blender_create_or_update_camera", {
    camera_name: "CodexShowcaseCamera",
    location: [4.7, -6.7, 3.8],
    rotation_euler: [1.12, 0, 0.62],
    lens_mm: 45,
    set_active: true
  });
  await callTool("blender_set_world", {
    color: [0.01, 0.012, 0.017],
    strength: 0.65
  });

  const preview = await callTool("blender_render_preview", {
    width: 768,
    height: 768,
    samples: 16,
    format: "jpeg",
    quality: 90
  });
  const image = preview.content?.find((item) => item.type === "image" && item.data);
  if (image?.data) {
    await mkdir(dirname(previewPath), { recursive: true });
    await writeFile(previewPath, Buffer.from(image.data, "base64"));
    console.log(`preview saved: ${previewPath}`);
  }

  await callTool("blender_save_copy", {
    relative_path: blendRelativePath,
    compress: true,
    create_directories: true
  });
  console.log(`blend saved: ${join(process.cwd(), blendRelativePath)}`);

  await transport.close();
};

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});

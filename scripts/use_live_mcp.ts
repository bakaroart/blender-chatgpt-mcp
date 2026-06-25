import { Buffer } from "node:buffer";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { CallToolResultSchema, ListToolsResultSchema } from "@modelcontextprotocol/sdk/types.js";

const serverUrl = process.env.MCP_URL ?? "http://127.0.0.1:3000/mcp";
const previewPath = join(process.cwd(), "dist", "live-preview.jpg");
const blendRelativePath = `dist/live-codex-demo-${new Date().toISOString().replace(/[:.]/g, "-")}.blend`;

type ToolResult = {
  content?: Array<{ type: string; text?: string; data?: string; mimeType?: string }>;
  structuredContent?: unknown;
};

const client = new Client({
  name: "blender-chatgpt-live-demo",
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

const sceneObjectNames = (result: ToolResult): string[] => {
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

  await callTool("blender_get_status", {});
  const before = await callTool("blender_get_scene_summary", { include_hidden: true, max_objects: 100 });
  const staleNames = sceneObjectNames(before).filter(
    (name) => name.startsWith("CodexLiveCube") || name === "CodexLiveKeyLight" || name === "CodexLiveCamera"
  );
  if (staleNames.length > 0) {
    await callTool("blender_delete_objects", {
      names: staleNames
    });
  }

  await callTool("blender_create_primitive", {
    primitive_type: "cube",
    name: "CodexLiveCube",
    location: [0, 0, 1],
    rotation_euler: [0, 0, 0.4],
    scale: [1.6, 1.6, 1.6],
    name_conflict: "unique"
  });
  await callTool("blender_create_or_update_material", {
    material_name: "CodexLiveBlue",
    base_color: [0.1, 0.35, 0.95, 1],
    metallic: 0.1,
    roughness: 0.42
  });
  await callTool("blender_assign_material", {
    object_name: "CodexLiveCube",
    material_name: "CodexLiveBlue",
    replace_existing: true
  });
  await callTool("blender_create_light", {
    name: "CodexLiveKeyLight",
    light_type: "area",
    location: [3, -4, 5],
    energy: 450,
    color: [1, 0.95, 0.9],
    size: 4
  });
  await callTool("blender_create_or_update_camera", {
    camera_name: "CodexLiveCamera",
    location: [4, -6, 4],
    rotation_euler: [1.1, 0, 0.58],
    lens_mm: 35,
    set_active: true
  });
  await callTool("blender_set_world", {
    color: [0.025, 0.03, 0.04],
    strength: 0.8
  });

  const preview = await callTool("blender_render_preview", {
    width: 512,
    height: 512,
    samples: 8,
    format: "jpeg",
    quality: 88
  });
  const image = preview.content?.find((item) => item.type === "image" && item.data);
  if (image?.data) {
    await mkdir(dirname(previewPath), { recursive: true });
    await writeFile(previewPath, Buffer.from(image.data, "base64"));
    console.log(`preview saved: ${previewPath}`);
  }

  await callTool("blender_get_scene_summary", {
    max_objects: 20
  });
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

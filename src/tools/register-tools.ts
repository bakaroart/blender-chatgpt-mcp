import type { McpServer, ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { BlenderBridgeClient } from "../bridge/client.js";
import type { AppConfig } from "../config.js";
import { cameraTools } from "./camera.js";
import { fileTools } from "./files.js";
import { lightTools } from "./lights.js";
import { materialTools } from "./materials.js";
import { objectTools } from "./objects.js";
import { renderTools } from "./render.js";
import { sceneTools } from "./scene.js";
import { makeToolHandler, type ToolDefinition } from "./common.js";
import { statusTools } from "./status.js";

export const TOOL_DEFINITIONS: ToolDefinition[] = [
  ...statusTools,
  ...objectTools,
  ...materialTools,
  ...lightTools,
  ...cameraTools,
  ...sceneTools,
  ...renderTools,
  ...fileTools
];

export const registerTools = (server: McpServer, client: BlenderBridgeClient, config: AppConfig): void => {
  for (const definition of TOOL_DEFINITIONS) {
    const handler = makeToolHandler(definition, client, {
      commandTimeoutMs: config.commandTimeoutMs,
      renderTimeoutMs: config.renderTimeoutMs
    }) as ToolCallback<typeof definition.inputSchema>;
    server.registerTool(
      definition.name,
      {
        title: definition.title,
        description: definition.description,
        inputSchema: definition.inputSchema,
        outputSchema: definition.outputSchema,
        annotations: definition.annotations
      },
      handler
    );
  }
};

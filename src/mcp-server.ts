import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { BlenderBridgeClient } from "./bridge/client.js";
import type { AppConfig } from "./config.js";
import { getPackageVersion } from "./package-info.js";
import { registerTools } from "./tools/register-tools.js";

export const SERVER_INSTRUCTIONS = [
  "Inspect the Blender scene before making changes.",
  "Use exact Blender object names returned by inspection tools.",
  "Prefer bounded tools and typed fields over broad edits.",
  "Render previews after meaningful visual changes when useful.",
  "Save only when explicitly asked by the user.",
  "Never infer that a change succeeded without a successful tool result.",
  "Avoid deletion unless the user clearly asks for it."
].join(" ");

export const createMcpServer = (client: BlenderBridgeClient, config: AppConfig): McpServer => {
  const server = new McpServer(
    {
      name: "blender-chatgpt-mcp",
      version: getPackageVersion(),
      description: SERVER_INSTRUCTIONS
    },
    {
      capabilities: {
        logging: {}
      }
    }
  );
  registerTools(server, client, config);
  return server;
};

import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { z } from "zod";
import { BridgeError } from "../errors.js";
import type { BlenderBridgeClient } from "../bridge/client.js";
import type { BridgeOperation } from "../bridge/protocol.js";

export interface ToolAnnotations {
  readOnlyHint: boolean;
  destructiveHint: boolean;
  openWorldHint: boolean;
  idempotentHint?: boolean;
}

export interface ToolDefinition {
  name: `blender_${string}`;
  title: string;
  description: string;
  operation: BridgeOperation;
  inputSchema: z.ZodType<unknown>;
  outputSchema: z.ZodType<unknown>;
  annotations: ToolAnnotations;
  readOnly: boolean;
  timeoutKind?: "normal" | "render";
  text: (result: unknown) => string;
}

export interface ToolHandlerOptions {
  commandTimeoutMs: number;
  renderTimeoutMs: number;
}

export type ToolResult = CallToolResult;

export const readOnlyAnnotations: ToolAnnotations = {
  readOnlyHint: true,
  destructiveHint: false,
  openWorldHint: false,
  idempotentHint: true
};

export const writeAnnotations: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: false,
  openWorldHint: false
};

export const destructiveAnnotations: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: true,
  openWorldHint: false
};

export const textFromObject = (prefix: string, result: unknown): string => {
  if (typeof result === "object" && result !== null && "name" in result && typeof result.name === "string") {
    return `${prefix}: ${result.name}`;
  }
  return prefix;
};

const stripPreviewImage = (value: unknown): unknown => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return value;
  }
  const record = value as Record<string, unknown>;
  const output: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(record)) {
    if (key !== "image_base64") {
      output[key] = item;
    }
  }
  return output;
};

export const makeToolHandler =
  (definition: ToolDefinition, client: BlenderBridgeClient, options: ToolHandlerOptions) =>
  async (rawArgs: unknown): Promise<ToolResult> => {
    const parsed = definition.inputSchema.safeParse(rawArgs ?? {});
    if (!parsed.success) {
      return {
        structuredContent: {
          ok: false,
          error: {
            code: "VALIDATION_ERROR",
            message: "Tool input did not match the required schema.",
            details: { issues: parsed.error.issues.map((issue) => ({ path: issue.path, message: issue.message })) }
          }
        },
        content: [{ type: "text", text: "Validation failed for Blender tool input." }],
        isError: true
      };
    }

    try {
      const bridge = await client.call(definition.operation, parsed.data, {
        readOnly: definition.readOnly,
        timeoutMs: definition.timeoutKind === "render" ? options.renderTimeoutMs : options.commandTimeoutMs
      });
      const renderRecord =
        definition.operation === "render_preview" && typeof bridge.result === "object" && bridge.result !== null
          ? (bridge.result as Record<string, unknown>)
          : undefined;
      const imageBase64 = renderRecord?.image_base64;
      const mimeType = renderRecord?.mime_type;
      const result = definition.operation === "render_preview" ? stripPreviewImage(bridge.result) : bridge.result;
      const content: CallToolResult["content"] = [{ type: "text", text: definition.text(result) }];
      if (typeof imageBase64 === "string" && typeof mimeType === "string") {
        content.push({ type: "image", data: imageBase64, mimeType });
      }
      return {
        structuredContent: {
          ok: true,
          result,
          warnings: bridge.warnings,
          request_id: bridge.requestId
        },
        content
      };
    } catch (error) {
      const bridgeError =
        error instanceof BridgeError
          ? error
          : new BridgeError({ code: "INTERNAL_ERROR", message: "Unexpected MCP tool failure." });
      return {
        structuredContent: {
          ok: false,
          error: {
            code: bridgeError.code,
            message: bridgeError.message,
            details: bridgeError.details ?? {}
          },
          request_id: bridgeError.requestId
        },
        content: [{ type: "text", text: `${bridgeError.code}: ${bridgeError.message}` }],
        isError: true
      };
    }
  };

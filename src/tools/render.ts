import { commonOutputSchema, renderPreviewSchema } from "../bridge/schemas.js";
import { readOnlyAnnotations, type ToolDefinition } from "./common.js";

export const renderTools: ToolDefinition[] = [
  {
    name: "blender_render_preview",
    title: "Render Blender Preview",
    description: "Render a bounded preview from the active or specified camera and return an MCP image content block plus metadata.",
    operation: "render_preview",
    inputSchema: renderPreviewSchema,
    outputSchema: commonOutputSchema,
    annotations: readOnlyAnnotations,
    readOnly: true,
    timeoutKind: "render",
    text: () => "Preview render completed."
  }
];

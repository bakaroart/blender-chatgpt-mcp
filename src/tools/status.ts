import { commonOutputSchema, getSceneSummarySchema, noInputSchema } from "../bridge/schemas.js";
import { readOnlyAnnotations, type ToolDefinition } from "./common.js";

export const statusTools: ToolDefinition[] = [
  {
    name: "blender_get_status",
    title: "Get Blender Bridge Status",
    description: "Inspect the local Blender bridge, active scene, render engine, object count, and project-root status.",
    operation: "get_status",
    inputSchema: noInputSchema,
    outputSchema: commonOutputSchema,
    annotations: readOnlyAnnotations,
    readOnly: true,
    text: () => "Blender status retrieved."
  },
  {
    name: "blender_get_scene_summary",
    title: "Get Blender Scene Summary",
    description: "Return a bounded summary of the active Blender scene without mesh geometry, animation curves, or custom properties.",
    operation: "get_scene_summary",
    inputSchema: getSceneSummarySchema,
    outputSchema: commonOutputSchema,
    annotations: readOnlyAnnotations,
    readOnly: true,
    text: () => "Blender scene summary retrieved."
  }
];

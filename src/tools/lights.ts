import { commonOutputSchema, createLightSchema, updateLightSchema } from "../bridge/schemas.js";
import { textFromObject, writeAnnotations, type ToolDefinition } from "./common.js";

export const lightTools: ToolDefinition[] = [
  {
    name: "blender_create_light",
    title: "Create Blender Light",
    description: "Create a point, sun, spot, or area light with bounded transform and light settings.",
    operation: "create_light",
    inputSchema: createLightSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: (result) => textFromObject("Light created", result)
  },
  {
    name: "blender_update_light",
    title: "Update Blender Light",
    description: "Update transform and typed light settings for one exact Blender light object.",
    operation: "update_light",
    inputSchema: updateLightSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Light updated."
  }
];

import { cameraSchema, commonOutputSchema } from "../bridge/schemas.js";
import { writeAnnotations, type ToolDefinition } from "./common.js";

export const cameraTools: ToolDefinition[] = [
  {
    name: "blender_create_or_update_camera",
    title: "Create Or Update Blender Camera",
    description: "Create or update a perspective or orthographic camera with bounded optics, clipping, transform, and active-camera selection.",
    operation: "create_or_update_camera",
    inputSchema: cameraSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Camera created or updated."
  }
];

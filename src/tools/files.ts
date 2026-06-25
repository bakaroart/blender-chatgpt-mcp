import { commonOutputSchema, saveCopySchema } from "../bridge/schemas.js";
import { writeAnnotations, type ToolDefinition } from "./common.js";

export const fileTools: ToolDefinition[] = [
  {
    name: "blender_save_copy",
    title: "Save Blender File Copy",
    description: "Save a copy of the current Blender file under the configured project root without overwriting existing files.",
    operation: "save_copy",
    inputSchema: saveCopySchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Blender file copy saved."
  }
];

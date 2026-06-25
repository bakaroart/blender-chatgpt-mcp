import { commonOutputSchema, setWorldSchema } from "../bridge/schemas.js";
import { writeAnnotations, type ToolDefinition } from "./common.js";

export const sceneTools: ToolDefinition[] = [
  {
    name: "blender_set_world",
    title: "Set Blender World",
    description: "Set only the active world's background color and/or strength.",
    operation: "set_world",
    inputSchema: setWorldSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "World background updated."
  }
];

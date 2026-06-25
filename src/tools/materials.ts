import { assignMaterialSchema, commonOutputSchema, materialSchema } from "../bridge/schemas.js";
import { writeAnnotations, type ToolDefinition } from "./common.js";

export const materialTools: ToolDefinition[] = [
  {
    name: "blender_create_or_update_material",
    title: "Create Or Update Blender Material",
    description: "Create or update a Principled BSDF material using only fixed, bounded material fields.",
    operation: "create_or_update_material",
    inputSchema: materialSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Material created or updated."
  },
  {
    name: "blender_assign_material",
    title: "Assign Blender Material",
    description: "Assign an existing material to a mesh-compatible object without deleting unrelated material datablocks.",
    operation: "assign_material",
    inputSchema: assignMaterialSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Material assigned."
  }
];

import {
  addModifierSchema,
  commonOutputSchema,
  createPrimitiveSchema,
  deleteObjectsSchema,
  duplicateObjectSchema,
  getObjectSchema,
  removeModifierSchema,
  renameObjectSchema,
  setTransformSchema,
  setVisibilitySchema
} from "../bridge/schemas.js";
import { destructiveAnnotations, readOnlyAnnotations, textFromObject, writeAnnotations, type ToolDefinition } from "./common.js";

export const objectTools: ToolDefinition[] = [
  {
    name: "blender_get_object",
    title: "Get Blender Object",
    description: "Return a detailed bounded summary for one exact Blender object name.",
    operation: "get_object",
    inputSchema: getObjectSchema,
    outputSchema: commonOutputSchema,
    annotations: readOnlyAnnotations,
    readOnly: true,
    text: (result) => textFromObject("Object retrieved", result)
  },
  {
    name: "blender_create_primitive",
    title: "Create Blender Primitive",
    description: "Create one bounded mesh primitive with explicit transform, name conflict behavior, and fixed primitive settings.",
    operation: "create_primitive",
    inputSchema: createPrimitiveSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: (result) => textFromObject("Primitive created", result)
  },
  {
    name: "blender_duplicate_object",
    title: "Duplicate Blender Object",
    description: "Duplicate one exact source object into a new exact object name with optional transform overrides.",
    operation: "duplicate_object",
    inputSchema: duplicateObjectSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: (result) => textFromObject("Object duplicated", result)
  },
  {
    name: "blender_rename_object",
    title: "Rename Blender Object",
    description: "Rename one exact Blender object, failing if the target name already exists.",
    operation: "rename_object",
    inputSchema: renameObjectSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Object renamed."
  },
  {
    name: "blender_set_transform",
    title: "Set Blender Object Transform",
    description: "Set location, Euler rotation, and/or scale for one exact Blender object name.",
    operation: "set_transform",
    inputSchema: setTransformSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Object transform updated."
  },
  {
    name: "blender_set_visibility",
    title: "Set Blender Object Visibility",
    description: "Set viewport and/or render visibility for one exact Blender object name.",
    operation: "set_visibility",
    inputSchema: setVisibilitySchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Object visibility updated."
  },
  {
    name: "blender_add_modifier",
    title: "Add Blender Modifier",
    description: "Add one allowlisted typed modifier to an exact Blender object.",
    operation: "add_modifier",
    inputSchema: addModifierSchema,
    outputSchema: commonOutputSchema,
    annotations: writeAnnotations,
    readOnly: false,
    text: () => "Modifier added."
  },
  {
    name: "blender_remove_modifier",
    title: "Remove Blender Modifier",
    description: "Remove one exact modifier from one exact Blender object after an undo checkpoint.",
    operation: "remove_modifier",
    inputSchema: removeModifierSchema,
    outputSchema: commonOutputSchema,
    annotations: destructiveAnnotations,
    readOnly: false,
    text: () => "Modifier removed."
  },
  {
    name: "blender_delete_objects",
    title: "Delete Blender Objects",
    description: "Delete one to fifty exact Blender object names after an undo checkpoint; wildcards and generic selectors are rejected.",
    operation: "delete_objects",
    inputSchema: deleteObjectsSchema,
    outputSchema: commonOutputSchema,
    annotations: destructiveAnnotations,
    readOnly: false,
    text: () => "Objects deleted."
  }
];

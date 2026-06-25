import { z } from "zod";
import { ERROR_CODES } from "../errors.js";

export const PROTOCOL_VERSION = "1.0.0";
export const MAX_BRIDGE_RESPONSE_BYTES = 5 * 1024 * 1024;
export const MAX_BRIDGE_REQUEST_BYTES = 1024 * 1024;

export const bridgeErrorSchema = z.object({
  code: z.enum(ERROR_CODES),
  message: z.string().max(512),
  details: z.record(z.string(), z.unknown()).optional().default({})
});

export const bridgeSuccessResponseSchema = z.object({
  ok: z.literal(true),
  request_id: z.string(),
  result: z.unknown(),
  warnings: z.array(z.string().max(512)).default([])
});

export const bridgeFailureResponseSchema = z.object({
  ok: z.literal(false),
  request_id: z.string().nullable().optional(),
  error: bridgeErrorSchema
});

export const bridgeResponseSchema = z.discriminatedUnion("ok", [
  bridgeSuccessResponseSchema,
  bridgeFailureResponseSchema
]);

export type BridgeSuccessResponse = z.infer<typeof bridgeSuccessResponseSchema>;
export type BridgeFailureResponse = z.infer<typeof bridgeFailureResponseSchema>;
export type BridgeResponse = z.infer<typeof bridgeResponseSchema>;

export const bridgeHealthSchema = z.object({
  ok: z.boolean(),
  bridge_version: z.string(),
  blender_version: z.string().nullable().optional(),
  status: z.string()
});

export type BridgeHealth = z.infer<typeof bridgeHealthSchema>;

export const bridgeStatusSchema = z.object({
  ok: z.boolean().optional(),
  bridge_version: z.string(),
  protocol_version: z.string().optional(),
  blender_version: z.string().nullable().optional(),
  status: z.string(),
  queue_depth: z.number().int().nonnegative().optional()
});

export type BridgeStatus = z.infer<typeof bridgeStatusSchema>;

export const operationNames = [
  "get_status",
  "get_scene_summary",
  "get_object",
  "create_primitive",
  "duplicate_object",
  "rename_object",
  "set_transform",
  "set_visibility",
  "create_or_update_material",
  "assign_material",
  "create_light",
  "update_light",
  "create_or_update_camera",
  "set_world",
  "add_modifier",
  "remove_modifier",
  "delete_objects",
  "render_preview",
  "save_copy"
] as const;

export type BridgeOperation = (typeof operationNames)[number];

import { z } from "zod";

export const MAX_NAME_LENGTH = 128;

const finite = z.number().finite();
const boundedNumber = (min: number, max: number) => finite.min(min).max(max);

export const nameSchema = z
  .string()
  .min(1)
  .max(MAX_NAME_LENGTH)
  .refine((value) => !value.includes("\0"), "Names must not contain null bytes.");

export const objectNameSchema = nameSchema.describe("Exact Blender object name.");
export const materialNameSchema = nameSchema.describe("Exact Blender material name.");
export const collectionNameSchema = nameSchema.describe("Exact Blender collection name.");

export const relativeBlendPathSchema = z
  .string()
  .min(1)
  .max(256)
  .refine((value) => !value.includes("\0"), "Path must not contain null bytes.")
  .refine((value) => !value.startsWith("/") && !/^[A-Za-z]:[\\/]/.test(value), "Path must be relative.")
  .refine((value) => value.split(/[\\/]/).every((part) => part !== ".."), "Path traversal is not allowed.")
  .refine((value) => value.toLowerCase().endsWith(".blend"), "Path must end in .blend.");

export const vector3Schema = z.array(boundedNumber(-1_000_000, 1_000_000)).length(3);
export const positiveVector3Schema = z.array(boundedNumber(-1_000_000, 1_000_000)).length(3);
export const colorRgbSchema = z.array(boundedNumber(0, 1)).length(3);
export const colorRgbaSchema = z.array(boundedNumber(0, 1)).length(4);

export const objectTypes = [
  "mesh",
  "curve",
  "surface",
  "meta",
  "font",
  "armature",
  "lattice",
  "empty",
  "light",
  "camera",
  "speaker",
  "volume",
  "grease_pencil"
] as const;

export const primitiveTypes = ["cube", "plane", "uv_sphere", "ico_sphere", "cylinder", "cone", "torus"] as const;
export const lightTypes = ["point", "sun", "spot", "area"] as const;
export const blendMethods = ["opaque", "blend", "hashed", "clip"] as const;

export const noInputSchema = z.object({}).strict();

export const getSceneSummarySchema = z
  .object({
    include_hidden: z.boolean().default(false),
    object_types: z.array(z.enum(objectTypes)).max(objectTypes.length).optional(),
    max_objects: z.number().int().min(1).max(500).default(100)
  })
  .strict();

export const getObjectSchema = z
  .object({
    name: objectNameSchema
  })
  .strict();

export const createPrimitiveSchema = z
  .object({
    primitive_type: z.enum(primitiveTypes),
    name: nameSchema,
    location: vector3Schema.default([0, 0, 0]),
    rotation_euler: vector3Schema.default([0, 0, 0]),
    scale: positiveVector3Schema.default([1, 1, 1]),
    collection_name: collectionNameSchema.optional(),
    name_conflict: z.enum(["error", "unique"]).default("error"),
    vertices: z.number().int().min(3).max(256).optional(),
    segments: z.number().int().min(3).max(256).optional(),
    ring_count: z.number().int().min(3).max(128).optional(),
    radius: boundedNumber(0.001, 10000).optional(),
    major_radius: boundedNumber(0.001, 10000).optional(),
    minor_radius: boundedNumber(0.001, 10000).optional(),
    depth: boundedNumber(0.001, 10000).optional()
  })
  .strict()
  .superRefine((value, context) => {
    const allowed: Record<(typeof primitiveTypes)[number], string[]> = {
      cube: [],
      plane: ["radius"],
      uv_sphere: ["segments", "ring_count", "radius"],
      ico_sphere: ["segments", "radius"],
      cylinder: ["vertices", "radius", "depth"],
      cone: ["vertices", "radius", "depth"],
      torus: ["major_radius", "minor_radius", "segments"]
    };
    const baseKeys = new Set([
      "primitive_type",
      "name",
      "location",
      "rotation_euler",
      "scale",
      "collection_name",
      "name_conflict",
      ...allowed[value.primitive_type]
    ]);
    for (const key of Object.keys(value)) {
      if (!baseKeys.has(key)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${key} is not supported for ${value.primitive_type}`,
          path: [key]
        });
      }
    }
  });

export const duplicateObjectSchema = z
  .object({
    source_name: objectNameSchema,
    new_name: nameSchema,
    linked_data: z.boolean().default(false),
    location: vector3Schema.optional(),
    rotation_euler: vector3Schema.optional(),
    scale: positiveVector3Schema.optional()
  })
  .strict();

export const renameObjectSchema = z
  .object({
    current_name: objectNameSchema,
    new_name: nameSchema
  })
  .strict();

export const setTransformSchema = z
  .object({
    name: objectNameSchema,
    location: vector3Schema.optional(),
    rotation_euler: vector3Schema.optional(),
    scale: positiveVector3Schema.optional(),
    allow_zero_scale: z.boolean().default(false)
  })
  .strict()
  .superRefine((value, context) => {
    if (!value.location && !value.rotation_euler && !value.scale) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "At least one transform field is required." });
    }
    if (value.scale && !value.allow_zero_scale && value.scale.some((component) => component === 0)) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "Zero scale requires allow_zero_scale=true.", path: ["scale"] });
    }
  });

export const setVisibilitySchema = z
  .object({
    name: objectNameSchema,
    hide_viewport: z.boolean().optional(),
    hide_render: z.boolean().optional()
  })
  .strict()
  .superRefine((value, context) => {
    if (value.hide_viewport === undefined && value.hide_render === undefined) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "At least one visibility field is required." });
    }
  });

export const materialSchema = z
  .object({
    material_name: materialNameSchema,
    create_if_missing: z.boolean().default(true),
    base_color: colorRgbaSchema.optional(),
    metallic: boundedNumber(0, 1).optional(),
    roughness: boundedNumber(0, 1).optional(),
    specular_ior_level: boundedNumber(0, 1).optional(),
    transmission_weight: boundedNumber(0, 1).optional(),
    alpha: boundedNumber(0, 1).optional(),
    emission_color: colorRgbSchema.optional(),
    emission_strength: boundedNumber(0, 1000).optional(),
    blend_method: z.enum(blendMethods).optional()
  })
  .strict();

export const assignMaterialSchema = z
  .object({
    object_name: objectNameSchema,
    material_name: materialNameSchema,
    slot_index: z.number().int().min(0).max(31).optional(),
    replace_existing: z.boolean().default(false)
  })
  .strict();

export const createLightSchema = z
  .object({
    name: nameSchema,
    light_type: z.enum(lightTypes),
    location: vector3Schema.default([0, 0, 0]),
    rotation_euler: vector3Schema.default([0, 0, 0]),
    energy: boundedNumber(0, 1_000_000).default(10),
    color: colorRgbSchema.default([1, 1, 1]),
    size: boundedNumber(0.001, 10000).optional(),
    radius: boundedNumber(0.001, 10000).optional(),
    spot_size: boundedNumber(0.001, Math.PI).optional(),
    spot_blend: boundedNumber(0, 1).optional()
  })
  .strict();

export const updateLightSchema = z
  .object({
    name: objectNameSchema,
    location: vector3Schema.optional(),
    rotation_euler: vector3Schema.optional(),
    energy: boundedNumber(0, 1_000_000).optional(),
    color: colorRgbSchema.optional(),
    size: boundedNumber(0.001, 10000).optional(),
    radius: boundedNumber(0.001, 10000).optional(),
    spot_size: boundedNumber(0.001, Math.PI).optional(),
    spot_blend: boundedNumber(0, 1).optional()
  })
  .strict();

export const cameraSchema = z
  .object({
    camera_name: nameSchema,
    create_if_missing: z.boolean().default(true),
    set_active: z.boolean().default(true),
    location: vector3Schema.optional(),
    rotation_euler: vector3Schema.optional(),
    lens_mm: boundedNumber(1, 500).optional(),
    sensor_width_mm: boundedNumber(1, 100).optional(),
    clip_start: boundedNumber(0.001, 10000).optional(),
    clip_end: boundedNumber(0.01, 1_000_000).optional(),
    camera_type: z.enum(["perspective", "orthographic"]).default("perspective"),
    ortho_scale: boundedNumber(0.001, 100000).optional()
  })
  .strict()
  .superRefine((value, context) => {
    if (value.clip_start !== undefined && value.clip_end !== undefined && value.clip_start >= value.clip_end) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "clip_start must be lower than clip_end." });
    }
  });

export const setWorldSchema = z
  .object({
    color: colorRgbSchema.optional(),
    strength: boundedNumber(0, 1000).optional()
  })
  .strict()
  .superRefine((value, context) => {
    if (!value.color && value.strength === undefined) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "At least one world field is required." });
    }
  });

export const addModifierSchema = z
  .discriminatedUnion("modifier_type", [
    z
      .object({
        object_name: objectNameSchema,
        modifier_type: z.literal("bevel"),
        modifier_name: nameSchema.optional(),
        width: boundedNumber(0, 10000).default(0.1),
        segments: z.number().int().min(1).max(64).default(1),
        limit_method: z.enum(["none", "angle", "weight"]).default("none")
      })
      .strict(),
    z
      .object({
        object_name: objectNameSchema,
        modifier_type: z.literal("subdivision_surface"),
        modifier_name: nameSchema.optional(),
        levels_viewport: z.number().int().min(0).max(6).default(1),
        levels_render: z.number().int().min(0).max(6).default(1),
        subdivision_type: z.enum(["catmull_clark", "simple"]).default("catmull_clark")
      })
      .strict(),
    z
      .object({
        object_name: objectNameSchema,
        modifier_type: z.literal("solidify"),
        modifier_name: nameSchema.optional(),
        thickness: boundedNumber(-10000, 10000).default(0.1),
        offset: boundedNumber(-1, 1).default(0)
      })
      .strict(),
    z
      .object({
        object_name: objectNameSchema,
        modifier_type: z.literal("mirror"),
        modifier_name: nameSchema.optional(),
        use_axis: z.array(z.boolean()).length(3).default([true, false, false]),
        merge: z.boolean().default(true),
        merge_threshold: boundedNumber(0, 100).default(0.001),
        mirror_object_name: objectNameSchema.optional()
      })
      .strict()
  ]);

export const removeModifierSchema = z
  .object({
    object_name: objectNameSchema,
    modifier_name: nameSchema
  })
  .strict();

export const deleteObjectsSchema = z
  .object({
    names: z
      .array(objectNameSchema)
      .min(1)
      .max(50)
      .superRefine((names, context) => {
        const seen = new Set<string>();
        for (const [index, name] of names.entries()) {
          if (seen.has(name)) {
            context.addIssue({ code: z.ZodIssueCode.custom, message: "Duplicate object names are not allowed.", path: [index] });
          }
          seen.add(name);
          if (/[*?[\]{}()|\\^$+]/.test(name)) {
            context.addIssue({ code: z.ZodIssueCode.custom, message: "Wildcards, globs, and regex syntax are not allowed.", path: [index] });
          }
        }
      })
  })
  .strict();

export const renderPreviewSchema = z
  .object({
    width: z.number().int().min(64).max(1024).default(512),
    height: z.number().int().min(64).max(1024).default(512),
    samples: z.number().int().min(1).max(64).default(16),
    format: z.enum(["jpeg", "png"]).default("jpeg"),
    quality: z.number().int().min(30).max(95).default(85),
    camera_name: objectNameSchema.optional(),
    transparent_background: z.boolean().default(false)
  })
  .strict()
  .superRefine((value, context) => {
    if (value.width * value.height > 1_048_576) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "Preview pixel count must not exceed 1,048,576." });
    }
  });

export const saveCopySchema = z
  .object({
    relative_path: relativeBlendPathSchema,
    compress: z.boolean().default(true),
    create_directories: z.boolean().default(false)
  })
  .strict();

export const commonOutputSchema = z.object({
  ok: z.boolean(),
  result: z.unknown().optional(),
  warnings: z.array(z.string()).optional(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
      details: z.record(z.string(), z.unknown()).optional()
    })
    .optional()
});

import { describe, expect, it } from "vitest";
import {
  createPrimitiveSchema,
  deleteObjectsSchema,
  renderPreviewSchema,
  saveCopySchema,
  setTransformSchema
} from "../../src/bridge/schemas.js";
import { TOOL_DEFINITIONS } from "../../src/tools/register-tools.js";

describe("tool schemas", () => {
  it("requires all tool annotations", () => {
    expect(TOOL_DEFINITIONS).toHaveLength(19);
    for (const tool of TOOL_DEFINITIONS) {
      expect(tool.annotations.readOnlyHint).toEqual(expect.any(Boolean));
      expect(tool.annotations.destructiveHint).toEqual(expect.any(Boolean));
      expect(tool.annotations.openWorldHint).toEqual(expect.any(Boolean));
    }
  });

  it("enforces render preview limits", () => {
    expect(renderPreviewSchema.safeParse({ width: 1024, height: 1024 }).success).toBe(true);
    expect(renderPreviewSchema.safeParse({ width: 1024, height: 1025 }).success).toBe(false);
    expect(renderPreviewSchema.safeParse({ width: 1024, height: 1024, samples: 65 }).success).toBe(false);
  });

  it("rejects unsafe delete selectors", () => {
    expect(deleteObjectsSchema.safeParse({ names: [] }).success).toBe(false);
    expect(deleteObjectsSchema.safeParse({ names: ["Cube", "Cube"] }).success).toBe(false);
    expect(deleteObjectsSchema.safeParse({ names: ["Cube*"] }).success).toBe(false);
    expect(deleteObjectsSchema.safeParse({ names: ["Cube"] }).success).toBe(true);
  });

  it("rejects path traversal and absolute save paths", () => {
    expect(saveCopySchema.safeParse({ relative_path: "../x.blend" }).success).toBe(false);
    expect(saveCopySchema.safeParse({ relative_path: "/tmp/x.blend" }).success).toBe(false);
    expect(saveCopySchema.safeParse({ relative_path: "renders/x.txt" }).success).toBe(false);
    expect(saveCopySchema.safeParse({ relative_path: "renders/x.blend" }).success).toBe(true);
  });

  it("rejects missing transform fields and zero scale by default", () => {
    expect(setTransformSchema.safeParse({ name: "Cube" }).success).toBe(false);
    expect(setTransformSchema.safeParse({ name: "Cube", scale: [1, 0, 1] }).success).toBe(false);
    expect(setTransformSchema.safeParse({ name: "Cube", scale: [1, 0, 1], allow_zero_scale: true }).success).toBe(true);
  });

  it("rejects irrelevant primitive-specific settings", () => {
    expect(createPrimitiveSchema.safeParse({ primitive_type: "cube", name: "Cube", vertices: 8 }).success).toBe(false);
    expect(createPrimitiveSchema.safeParse({ primitive_type: "cylinder", name: "Cylinder", vertices: 16 }).success).toBe(true);
  });
});

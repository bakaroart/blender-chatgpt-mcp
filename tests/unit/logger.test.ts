import { describe, expect, it } from "vitest";
import { redactForLog } from "../../src/logger.js";

describe("logger redaction", () => {
  it("redacts token-like keys and bearer values", () => {
    expect(
      redactForLog({
        Authorization: "Bearer abcdefghijklmnopqrstuvwxyz0123456789",
        nested: { bridge_token: "secret" }
      })
    ).toEqual({
      Authorization: "[redacted]",
      nested: { bridge_token: "[redacted]" }
    });
  });

  it("redacts large base64-like strings", () => {
    expect(redactForLog("a".repeat(300))).toBe("[redacted-large-string]");
  });
});

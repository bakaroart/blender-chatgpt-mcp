import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { BlenderBridgeClient } from "../../src/bridge/client.js";
import { createLogger } from "../../src/logger.js";
import { TOOL_DEFINITIONS } from "../../src/tools/register-tools.js";
import { makeToolHandler } from "../../src/tools/common.js";
import { startFakeBridge, type FakeBridge } from "../fake_bridge/server.js";

describe("fake bridge integration", () => {
  let bridge: FakeBridge;
  let client: BlenderBridgeClient;

  beforeEach(async () => {
    bridge = await startFakeBridge();
    client = new BlenderBridgeClient({
      bridgeUrl: bridge.url,
      token: "test-token",
      commandTimeoutMs: 100,
      renderTimeoutMs: 100,
      logger: createLogger("error"),
      maxResponseBytes: 1024 * 1024
    });
  });

  afterEach(async () => {
    await bridge.close();
  });

  it("runs a successful tool handler against the fake bridge", async () => {
    const definition = TOOL_DEFINITIONS.find((tool) => tool.name === "blender_get_status");
    expect(definition).toBeDefined();
    const result = await makeToolHandler(definition!, client, { commandTimeoutMs: 100, renderTimeoutMs: 100 })({});
    expect(result.structuredContent?.ok).toBe(true);
    expect(result.content[0]).toMatchObject({ type: "text" });
  });

  it("distinguishes readyz-style authenticated status", async () => {
    await expect(client.status()).resolves.toMatchObject({ status: "running" });
    bridge.setMode("auth_failure");
    await expect(client.status()).rejects.toMatchObject({ code: "AUTH_INVALID" });
  });

  it("handles delayed timeout", async () => {
    bridge.setMode("delay");
    await expect(client.call("get_status", {}, { readOnly: true, timeoutMs: 20 })).rejects.toMatchObject({
      code: "COMMAND_TIMEOUT"
    });
  });

  it("handles malformed JSON, mismatched IDs, oversized responses, bridge errors, and dropped connections", async () => {
    bridge.setMode("malformed_json");
    await expect(client.call("get_status", {}, { readOnly: true })).rejects.toMatchObject({ code: "INVALID_JSON" });
    bridge.setMode("mismatch");
    await expect(client.call("get_status", {}, { readOnly: true })).rejects.toMatchObject({ code: "REQUEST_ID_MISMATCH" });
    bridge.setMode("oversized");
    await expect(client.call("get_status", {}, { readOnly: true })).rejects.toMatchObject({ code: "RESPONSE_TOO_LARGE" });
    bridge.setMode("bridge_error");
    await expect(client.call("get_object", { name: "Missing" }, { readOnly: true })).rejects.toMatchObject({
      code: "OBJECT_NOT_FOUND"
    });
    bridge.setMode("drop");
    await expect(client.call("get_status", {}, { readOnly: true })).rejects.toMatchObject({ code: "BRIDGE_UNAVAILABLE" });
  });
});

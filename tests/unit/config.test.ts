import { describe, expect, it } from "vitest";
import { loadConfig } from "../../src/config.js";
import { ConfigError } from "../../src/errors.js";

const baseEnv = {
  BLENDER_BRIDGE_TOKEN: "x".repeat(43)
};

describe("config", () => {
  it("defaults to loopback MCP and Blender bridge addresses", () => {
    const config = loadConfig(baseEnv);
    expect(config.mcpHost).toBe("127.0.0.1");
    expect(config.mcpPort).toBe(3000);
    expect(config.blenderBridgeUrl.href).toBe("http://127.0.0.1:8765/");
  });

  it("fails fast when token is missing", () => {
    expect(() => loadConfig({})).toThrow(ConfigError);
  });

  it("rejects non-loopback bridge URLs unless explicitly overridden", () => {
    expect(() =>
      loadConfig({
        ...baseEnv,
        BLENDER_BRIDGE_URL: "http://192.168.1.10:8765"
      })
    ).toThrow(/localhost/);
    expect(
      loadConfig({
        ...baseEnv,
        BLENDER_BRIDGE_URL: "http://192.168.1.10:8765",
        BLENDER_ALLOW_UNSAFE_BRIDGE_URL: "1"
      }).unsafeBridgeUrlOverride
    ).toBe(true);
  });

  it("rejects invalid ports and timeouts", () => {
    expect(() => loadConfig({ ...baseEnv, MCP_PORT: "0" })).toThrow(/MCP_PORT/);
    expect(() => loadConfig({ ...baseEnv, BLENDER_COMMAND_TIMEOUT_MS: "1" })).toThrow(/BLENDER_COMMAND_TIMEOUT_MS/);
  });
});

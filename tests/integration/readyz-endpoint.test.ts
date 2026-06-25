import http from "node:http";
import type { AddressInfo } from "node:net";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { BlenderBridgeClient } from "../../src/bridge/client.js";
import type { AppConfig } from "../../src/config.js";
import { createLogger } from "../../src/logger.js";
import { createExpressApp } from "../../src/transport.js";
import { startFakeBridge, type FakeBridge } from "../fake_bridge/server.js";

const listen = async (server: http.Server): Promise<URL> => {
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address() as AddressInfo;
  return new URL(`http://127.0.0.1:${address.port}`);
};

describe("readyz endpoint", () => {
  let bridge: FakeBridge | undefined;
  let server: http.Server | undefined;
  let baseUrl: URL;

  beforeEach(async () => {
    bridge = await startFakeBridge("ready-token");
    const config: AppConfig = {
      mcpHost: "127.0.0.1",
      mcpPort: 0,
      mcpPath: "/mcp",
      blenderBridgeUrl: bridge.url,
      blenderBridgeToken: "ready-token",
      commandTimeoutMs: 100,
      renderTimeoutMs: 100,
      logLevel: "error",
      unsafeBridgeUrlOverride: false
    };
    const client = new BlenderBridgeClient({
      bridgeUrl: bridge.url,
      token: "ready-token",
      commandTimeoutMs: 100,
      renderTimeoutMs: 100,
      logger: createLogger("error")
    });
    server = http.createServer(createExpressApp(config, client, createLogger("error")));
    baseUrl = await listen(server);
  });

  afterEach(async () => {
    if (server) {
      await new Promise<void>((resolve, reject) => server?.close((error) => (error ? reject(error) : resolve())));
    }
    if (bridge) {
      await bridge.close();
    }
  });

  it("distinguishes available, invalid token, and unavailable bridge states", async () => {
    let response = await fetch(new URL("/readyz", baseUrl));
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ ok: true, bridge: "available_authenticated" });

    bridge?.setMode("auth_failure");
    response = await fetch(new URL("/readyz", baseUrl));
    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toMatchObject({ bridge: "authentication_failed" });

    await bridge?.close();
    bridge = undefined;
    response = await fetch(new URL("/readyz", baseUrl));
    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toMatchObject({ bridge: "unavailable" });
  });
});

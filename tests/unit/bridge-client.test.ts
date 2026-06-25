import { describe, expect, it, vi } from "vitest";
import { BlenderBridgeClient } from "../../src/bridge/client.js";
import { BridgeError } from "../../src/errors.js";
import { createLogger } from "../../src/logger.js";

const makeClient = () =>
  new BlenderBridgeClient({
    bridgeUrl: new URL("http://127.0.0.1:8765"),
    token: "token-value",
    commandTimeoutMs: 1000,
    renderTimeoutMs: 1000,
    logger: createLogger("error"),
    maxResponseBytes: 2048
  });

const parseRequestBody = (init?: RequestInit): { request_id: string } => {
  if (typeof init?.body !== "string") {
    throw new TypeError("Expected string request body.");
  }
  return JSON.parse(init.body) as { request_id: string };
};

describe("BlenderBridgeClient", () => {
  it("creates an authorization header without exposing it in results", () => {
    expect(makeClient().authHeaders()).toMatchObject({ Authorization: "Bearer token-value" });
  });

  it("detects request ID mismatches", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true, request_id: "wrong", result: {}, warnings: [] }))));
    vi.stubGlobal("fetch", fetchMock);
    await expect(makeClient().call("get_status", {}, { readOnly: true })).rejects.toMatchObject({
      code: "REQUEST_ID_MISMATCH"
    });
  });

  it("maps bridge error responses safely", async () => {
    const fetchMock = vi.fn((_url: string | URL | Request, init?: RequestInit) => {
      const body = parseRequestBody(init);
      return new Response(
        JSON.stringify({
          ok: false,
          request_id: body.request_id,
          error: { code: "OBJECT_NOT_FOUND", message: "Object not found.", details: {} }
        }),
        { status: 409 }
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(makeClient().call("get_object", { name: "Missing" }, { readOnly: true })).rejects.toMatchObject({
      code: "OBJECT_NOT_FOUND",
      status: 409
    });
  });

  it("retries transient read-only connection failures once", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("dropped"))
      .mockImplementationOnce((_url: string | URL | Request, init?: RequestInit) => {
        const body = parseRequestBody(init);
        return new Response(JSON.stringify({ ok: true, request_id: body.request_id, result: { ok: true }, warnings: [] }));
      });
    vi.stubGlobal("fetch", fetchMock);
    await expect(makeClient().call("get_status", {}, { readOnly: true })).resolves.toMatchObject({
      result: { ok: true }
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does not retry mutating calls after ambiguous failures", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("dropped"));
    vi.stubGlobal("fetch", fetchMock);
    await expect(makeClient().call("create_primitive", { name: "Cube" }, { readOnly: false })).rejects.toBeInstanceOf(
      BridgeError
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("enforces response-size limits from content-length", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response("{}", { headers: { "content-length": "4096" } })));
    vi.stubGlobal("fetch", fetchMock);
    await expect(makeClient().call("get_status", {}, { readOnly: true })).rejects.toMatchObject({
      code: "RESPONSE_TOO_LARGE"
    });
  });
});

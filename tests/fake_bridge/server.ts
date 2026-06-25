import http from "node:http";
import type { AddressInfo } from "node:net";

export type FakeBridgeMode =
  | "success"
  | "auth_failure"
  | "delay"
  | "malformed_json"
  | "mismatch"
  | "oversized"
  | "bridge_error"
  | "drop";

export interface FakeBridge {
  url: URL;
  setMode: (mode: FakeBridgeMode) => void;
  close: () => Promise<void>;
}

export const startFakeBridge = async (token = "test-token"): Promise<FakeBridge> => {
  let mode: FakeBridgeMode = "success";
  const server = http.createServer((req, res) => {
    if (req.url === "/healthz") {
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ ok: true, bridge_version: "0.1.0", blender_version: "fake", status: "running" }));
      return;
    }
    if (req.url === "/v1/status") {
      if (req.headers.authorization !== `Bearer ${token}` || mode === "auth_failure") {
        res.statusCode = 401;
        res.end(JSON.stringify({ ok: false, error: { code: "AUTH_INVALID", message: "bad", details: {} } }));
        return;
      }
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ ok: true, bridge_version: "0.1.0", protocol_version: "1.0.0", blender_version: "fake", status: "running" }));
      return;
    }
    if (req.url !== "/v1/commands" || req.method !== "POST") {
      res.statusCode = 404;
      res.end();
      return;
    }
    if (mode === "drop") {
      req.socket.destroy();
      return;
    }
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      if (req.headers.authorization !== `Bearer ${token}` || mode === "auth_failure") {
        res.statusCode = 401;
        res.end(JSON.stringify({ ok: false, request_id: null, error: { code: "AUTH_INVALID", message: "bad token", details: {} } }));
        return;
      }
      if (mode === "malformed_json") {
        res.end("{not json");
        return;
      }
      if (mode === "oversized") {
        res.setHeader("content-length", String(10 * 1024 * 1024));
        res.end("{}");
        return;
      }
      const body = JSON.parse(Buffer.concat(chunks).toString("utf8")) as { request_id: string; operation: string };
      const send = () => {
        if (mode === "mismatch") {
          res.end(JSON.stringify({ ok: true, request_id: "00000000-0000-4000-8000-000000000000", result: {}, warnings: [] }));
          return;
        }
        if (mode === "bridge_error") {
          res.statusCode = 409;
          res.end(
            JSON.stringify({
              ok: false,
              request_id: body.request_id,
              error: { code: "OBJECT_NOT_FOUND", message: "Object not found.", details: {} }
            })
          );
          return;
        }
        res.setHeader("content-type", "application/json");
        res.end(
          JSON.stringify({
            ok: true,
            request_id: body.request_id,
            result: { operation: body.operation, name: "FakeObject" },
            warnings: []
          })
        );
      };
      if (mode === "delay") {
        setTimeout(send, 200);
      } else {
        send();
      }
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address() as AddressInfo;
  return {
    url: new URL(`http://127.0.0.1:${address.port}`),
    setMode: (next) => {
      mode = next;
    },
    close: async () => {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      });
    }
  };
};

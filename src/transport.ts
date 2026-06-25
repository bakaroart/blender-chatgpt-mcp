import http from "node:http";
import type { AddressInfo } from "node:net";
import express, { type NextFunction, type Request, type Response } from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { StreamableHTTPServerTransportOptions } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import type { BlenderBridgeClient } from "./bridge/client.js";
import type { AppConfig } from "./config.js";
import { isLoopbackHost } from "./config.js";
import { BridgeError } from "./errors.js";
import type { Logger } from "./logger.js";
import { createMcpServer } from "./mcp-server.js";
import { getPackageVersion } from "./package-info.js";

export interface RunningHttpServer {
  url: string;
  close: () => Promise<void>;
}

const allowedHost = (configuredHost: string, hostHeader: string | undefined): boolean => {
  if (!hostHeader) {
    return true;
  }
  const host = hostHeader.replace(/:\d+$/, "").replace(/^\[|\]$/g, "");
  return isLoopbackHost(host) || host === configuredHost;
};

const hostValidation =
  (configuredHost: string) =>
  (req: Request, res: Response, next: NextFunction): void => {
    if (!allowedHost(configuredHost, req.headers.host)) {
      res.status(403).json({ ok: false, error: "Host header is not allowed." });
      return;
    }
    next();
  };

const jsonErrorHandler = (error: unknown, _req: Request, res: Response, next: NextFunction): void => {
  if (!error) {
    next();
    return;
  }
  const status = typeof error === "object" && error !== null && "status" in error ? Number(error.status) : 400;
  res.status(status === 413 ? 413 : 400).json({
    ok: false,
    error: status === 413 ? "REQUEST_TOO_LARGE" : "INVALID_JSON"
  });
};

export const createExpressApp = (config: AppConfig, client: BlenderBridgeClient, logger: Logger): express.Express => {
  const app = express();
  app.disable("x-powered-by");
  app.use(hostValidation(config.mcpHost));
  app.use(express.json({ limit: "1mb", type: ["application/json", "application/*+json"] }));
  app.use(jsonErrorHandler);

  app.get("/healthz", (_req, res) => {
    res.json({
      ok: true,
      name: "blender-chatgpt-mcp",
      version: getPackageVersion(),
      status: "running"
    });
  });

  app.get("/readyz", async (_req, res) => {
    try {
      const status = await client.status();
      res.json({
        ok: true,
        bridge: "available_authenticated",
        bridge_status: status.status,
        protocol_version: status.protocol_version
      });
    } catch (error) {
      if (error instanceof BridgeError && error.code === "AUTH_INVALID") {
        res.status(401).json({ ok: false, bridge: "authentication_failed", error_code: error.code });
        return;
      }
      res.status(503).json({
        ok: false,
        bridge: "unavailable",
        error_code: error instanceof BridgeError ? error.code : "BRIDGE_UNAVAILABLE"
      });
    }
  });

  app.post(config.mcpPath, async (req, res) => {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined
    } as unknown as StreamableHTTPServerTransportOptions);
    const server = createMcpServer(client, config);
    try {
      await server.connect(transport as unknown as Transport);
      await transport.handleRequest(req, res, req.body);
      res.on("close", () => {
        void transport.close().catch((error: unknown) => {
          logger.warn("transport_close_failed", { error });
        });
        void server.close().catch((error: unknown) => {
          logger.warn("mcp_server_close_failed", { error });
        });
      });
    } catch (error) {
      logger.error("mcp_request_failed", { error });
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null
        });
      }
    }
  });

  app.get(config.mcpPath, (_req, res) => {
    res.status(405).json({
      jsonrpc: "2.0",
      error: { code: -32000, message: "Method not allowed for stateless Streamable HTTP." },
      id: null
    });
  });

  app.delete(config.mcpPath, (_req, res) => {
    res.status(405).json({
      jsonrpc: "2.0",
      error: { code: -32000, message: "Method not allowed for stateless Streamable HTTP." },
      id: null
    });
  });

  return app;
};

export const startHttpServer = async (
  config: AppConfig,
  client: BlenderBridgeClient,
  logger: Logger
): Promise<RunningHttpServer> => {
  if (!isLoopbackHost(config.mcpHost)) {
    logger.warn("non_loopback_mcp_bind", {
      host: config.mcpHost,
      warning: "Public deployment is unsupported in the MVP without OAuth 2.1 and production hardening."
    });
  }
  const app = createExpressApp(config, client, logger);
  const server = http.createServer(app);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(config.mcpPort, config.mcpHost, () => {
      server.off("error", reject);
      resolve();
    });
  });
  const address = server.address() as AddressInfo;
  const url = `http://${config.mcpHost}:${address.port}${config.mcpPath}`;
  logger.info("mcp_server_started", { host: config.mcpHost, port: address.port, path: config.mcpPath });

  return {
    url,
    close: async () => {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });
    }
  };
};

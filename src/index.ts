#!/usr/bin/env node
import "dotenv/config";
import { BlenderBridgeClient } from "./bridge/client.js";
import { loadConfig } from "./config.js";
import { ConfigError } from "./errors.js";
import { createLogger } from "./logger.js";
import { startHttpServer } from "./transport.js";

const main = async (): Promise<void> => {
  let config;
  try {
    config = loadConfig();
  } catch (error) {
    const message = error instanceof ConfigError ? error.message : "Configuration failed.";
    console.error(JSON.stringify({ timestamp: new Date().toISOString(), level: "error", message }));
    process.exitCode = 1;
    return;
  }
  const logger = createLogger(config.logLevel);
  const client = new BlenderBridgeClient({
    bridgeUrl: config.blenderBridgeUrl,
    token: config.blenderBridgeToken,
    commandTimeoutMs: config.commandTimeoutMs,
    renderTimeoutMs: config.renderTimeoutMs,
    logger
  });
  const running = await startHttpServer(config, client, logger);
  logger.info("startup_complete", { mcp_url: running.url });

  const shutdown = async (signal: NodeJS.Signals): Promise<void> => {
    logger.info("shutdown_started", { signal });
    await running.close();
    logger.info("shutdown_complete", { signal });
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT").finally(() => process.exit(0));
  });
  process.once("SIGTERM", () => {
    void shutdown("SIGTERM").finally(() => process.exit(0));
  });
};

void main();

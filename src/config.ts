import { z } from "zod";
import { ConfigError } from "./errors.js";
import type { LogLevel } from "./logger.js";

const DEFAULTS = {
  MCP_HOST: "127.0.0.1",
  MCP_PORT: "3000",
  MCP_PATH: "/mcp",
  BLENDER_BRIDGE_URL: "http://127.0.0.1:8765",
  BLENDER_COMMAND_TIMEOUT_MS: "30000",
  BLENDER_RENDER_TIMEOUT_MS: "120000",
  LOG_LEVEL: "info"
} as const;

export interface AppConfig {
  mcpHost: string;
  mcpPort: number;
  mcpPath: string;
  blenderBridgeUrl: URL;
  blenderBridgeToken: string;
  commandTimeoutMs: number;
  renderTimeoutMs: number;
  logLevel: LogLevel;
  unsafeBridgeUrlOverride: boolean;
}

const logLevelSchema = z.enum(["debug", "info", "warn", "error"]);

const parseIntInRange = (name: string, raw: string | undefined, min: number, max: number): number => {
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new ConfigError(`${name} must be an integer from ${min} through ${max}.`);
  }
  return parsed;
};

export const isLoopbackHost = (host: string): boolean => {
  const normalized = host.replace(/^\[|\]$/g, "").toLowerCase();
  return (
    normalized === "localhost" ||
    normalized === "::1" ||
    normalized === "0:0:0:0:0:0:0:1" ||
    normalized.startsWith("127.")
  );
};

const parseUrl = (raw: string): URL => {
  try {
    return new URL(raw);
  } catch {
    throw new ConfigError("BLENDER_BRIDGE_URL must be a valid URL.");
  }
};

const parsePath = (path: string): string => {
  if (!path.startsWith("/") || path.includes("\0") || path.includes("?") || path.includes("#")) {
    throw new ConfigError("MCP_PATH must be an absolute HTTP path.");
  }
  return path;
};

export const loadConfig = (env: NodeJS.ProcessEnv = process.env): AppConfig => {
  const mcpHost = env.MCP_HOST ?? DEFAULTS.MCP_HOST;
  const mcpPort = parseIntInRange("MCP_PORT", env.MCP_PORT ?? DEFAULTS.MCP_PORT, 1, 65535);
  const mcpPath = parsePath(env.MCP_PATH ?? DEFAULTS.MCP_PATH);
  const bridgeUrl = parseUrl(env.BLENDER_BRIDGE_URL ?? DEFAULTS.BLENDER_BRIDGE_URL);
  const token = env.BLENDER_BRIDGE_TOKEN ?? "";
  const unsafeBridgeUrlOverride = env.BLENDER_ALLOW_UNSAFE_BRIDGE_URL === "1";

  if (bridgeUrl.protocol !== "http:") {
    throw new ConfigError("BLENDER_BRIDGE_URL must use http:// for the local bridge.");
  }
  if (!isLoopbackHost(bridgeUrl.hostname) && !unsafeBridgeUrlOverride) {
    throw new ConfigError(
      "BLENDER_BRIDGE_URL must point at localhost/127.0.0.1 unless BLENDER_ALLOW_UNSAFE_BRIDGE_URL=1 is set for development."
    );
  }
  if (token.trim().length === 0) {
    throw new ConfigError("BLENDER_BRIDGE_TOKEN is required. Generate it in the Blender add-on preferences.");
  }

  const commandTimeoutMs = parseIntInRange(
    "BLENDER_COMMAND_TIMEOUT_MS",
    env.BLENDER_COMMAND_TIMEOUT_MS ?? DEFAULTS.BLENDER_COMMAND_TIMEOUT_MS,
    100,
    300000
  );
  const renderTimeoutMs = parseIntInRange(
    "BLENDER_RENDER_TIMEOUT_MS",
    env.BLENDER_RENDER_TIMEOUT_MS ?? DEFAULTS.BLENDER_RENDER_TIMEOUT_MS,
    1000,
    600000
  );
  const logLevel = logLevelSchema.parse(env.LOG_LEVEL ?? DEFAULTS.LOG_LEVEL);

  return {
    mcpHost,
    mcpPort,
    mcpPath,
    blenderBridgeUrl: bridgeUrl,
    blenderBridgeToken: token,
    commandTimeoutMs,
    renderTimeoutMs,
    logLevel,
    unsafeBridgeUrlOverride
  };
};

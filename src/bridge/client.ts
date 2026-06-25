import { randomUUID } from "node:crypto";
import { BridgeError, normalizeErrorCode } from "../errors.js";
import type { Logger } from "../logger.js";
import {
  bridgeHealthSchema,
  bridgeResponseSchema,
  bridgeStatusSchema,
  MAX_BRIDGE_RESPONSE_BYTES,
  PROTOCOL_VERSION,
  type BridgeHealth,
  type BridgeOperation,
  type BridgeStatus
} from "./protocol.js";

export interface BridgeClientOptions {
  bridgeUrl: URL;
  token: string;
  commandTimeoutMs: number;
  renderTimeoutMs: number;
  logger: Logger;
  maxResponseBytes?: number;
  userAgent?: string;
}

export interface BridgeCallOptions {
  readOnly: boolean;
  timeoutMs?: number;
}

export interface BridgeCommandResult {
  requestId: string;
  result: unknown;
  warnings: string[];
}

export class BlenderBridgeClient {
  private readonly bridgeUrl: URL;
  private readonly token: string;
  private readonly commandTimeoutMs: number;
  private readonly renderTimeoutMs: number;
  private readonly logger: Logger;
  private readonly maxResponseBytes: number;
  private readonly userAgent: string;

  constructor(options: BridgeClientOptions) {
    this.bridgeUrl = options.bridgeUrl;
    this.token = options.token;
    this.commandTimeoutMs = options.commandTimeoutMs;
    this.renderTimeoutMs = options.renderTimeoutMs;
    this.logger = options.logger;
    this.maxResponseBytes = options.maxResponseBytes ?? MAX_BRIDGE_RESPONSE_BYTES;
    this.userAgent = options.userAgent ?? "blender-chatgpt-mcp/0.1.0";
  }

  async health(): Promise<BridgeHealth> {
    const url = new URL("/healthz", this.bridgeUrl);
    const response = await fetch(url, {
      method: "GET",
      headers: { "User-Agent": this.userAgent }
    });
    const json = await this.readJson(response, 128 * 1024);
    return bridgeHealthSchema.parse(json);
  }

  async status(): Promise<BridgeStatus> {
    const url = new URL("/v1/status", this.bridgeUrl);
    const response = await fetch(url, {
      method: "GET",
      headers: this.authHeaders()
    });
    if (response.status === 401) {
      throw new BridgeError({ code: "AUTH_INVALID", message: "Blender bridge authentication failed.", status: 401 });
    }
    const json = await this.readJson(response, this.maxResponseBytes);
    return bridgeStatusSchema.parse(json);
  }

  async call(operation: BridgeOperation, args: unknown, options: BridgeCallOptions): Promise<BridgeCommandResult> {
    const requestId = randomUUID();
    const timeoutMs = options.timeoutMs ?? this.defaultTimeout(operation);
    const attempt = async (): Promise<BridgeCommandResult> => {
      const started = Date.now();
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const url = new URL("/v1/commands", this.bridgeUrl);
        const response = await fetch(url, {
          method: "POST",
          headers: {
            ...this.authHeaders(),
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            request_id: requestId,
            protocol_version: PROTOCOL_VERSION,
            operation,
            args
          }),
          signal: controller.signal
        });
        const payload = bridgeResponseSchema.parse(await this.readJson(response, this.maxResponseBytes));
        if (payload.request_id && payload.request_id !== requestId) {
          throw new BridgeError({
            code: "REQUEST_ID_MISMATCH",
            message: "Blender bridge returned a mismatched request ID.",
            status: response.status,
            requestId
          });
        }
        if (!payload.ok) {
          throw new BridgeError({
            code: normalizeErrorCode(payload.error.code),
            message: payload.error.message,
            status: response.status,
            details: payload.error.details,
            requestId
          });
        }
        this.logger.info("bridge_command", {
          request_id: requestId,
          operation,
          duration_ms: Date.now() - started,
          success: true
        });
        return {
          requestId,
          result: payload.result,
          warnings: payload.warnings
        };
      } catch (error) {
        if (error instanceof BridgeError) {
          this.logger.warn("bridge_command", {
            request_id: requestId,
            operation,
            duration_ms: Date.now() - started,
            success: false,
            error_code: error.code
          });
          throw error;
        }
        const code = error instanceof DOMException && error.name === "AbortError" ? "COMMAND_TIMEOUT" : "BRIDGE_UNAVAILABLE";
        this.logger.warn("bridge_command", {
          request_id: requestId,
          operation,
          duration_ms: Date.now() - started,
          success: false,
          error_code: code
        });
        throw new BridgeError({
          code,
          message: code === "COMMAND_TIMEOUT" ? "Blender bridge command timed out." : "Blender bridge is unavailable.",
          requestId
        });
      } finally {
        clearTimeout(timeout);
      }
    };

    try {
      return await attempt();
    } catch (error) {
      if (options.readOnly && error instanceof BridgeError && error.code === "BRIDGE_UNAVAILABLE") {
        return attempt();
      }
      throw error;
    }
  }

  authHeaders(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.token}`,
      "User-Agent": this.userAgent
    };
  }

  private defaultTimeout(operation: BridgeOperation): number {
    return operation === "render_preview" ? this.renderTimeoutMs : this.commandTimeoutMs;
  }

  private async readJson(response: Response, maxBytes: number): Promise<unknown> {
    const contentLength = response.headers.get("content-length");
    if (contentLength && Number(contentLength) > maxBytes) {
      throw new BridgeError({
        code: "RESPONSE_TOO_LARGE",
        message: "Blender bridge response exceeded the configured size limit.",
        status: response.status
      });
    }
    const text = await response.text();
    if (Buffer.byteLength(text, "utf8") > maxBytes) {
      throw new BridgeError({
        code: "RESPONSE_TOO_LARGE",
        message: "Blender bridge response exceeded the configured size limit.",
        status: response.status
      });
    }
    try {
      return JSON.parse(text) as unknown;
    } catch {
      throw new BridgeError({
        code: "INVALID_JSON",
        message: "Blender bridge returned invalid JSON.",
        status: response.status
      });
    }
  }
}

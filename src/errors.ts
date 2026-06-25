export const ERROR_CODES = [
  "AUTH_REQUIRED",
  "AUTH_INVALID",
  "REQUEST_TOO_LARGE",
  "INVALID_JSON",
  "INVALID_REQUEST",
  "UNSUPPORTED_OPERATION",
  "VALIDATION_ERROR",
  "QUEUE_FULL",
  "COMMAND_TIMEOUT",
  "BRIDGE_STOPPING",
  "OBJECT_NOT_FOUND",
  "OBJECT_NAME_CONFLICT",
  "MATERIAL_NOT_FOUND",
  "INVALID_OBJECT_TYPE",
  "CAMERA_NOT_FOUND",
  "PROJECT_ROOT_NOT_CONFIGURED",
  "PATH_OUTSIDE_PROJECT_ROOT",
  "TARGET_ALREADY_EXISTS",
  "RENDER_FAILED",
  "BLENDER_CONTEXT_ERROR",
  "PROTOCOL_VERSION_MISMATCH",
  "INTERNAL_ERROR",
  "BRIDGE_UNAVAILABLE",
  "RESPONSE_TOO_LARGE",
  "REQUEST_ID_MISMATCH"
] as const;

export type ErrorCode = (typeof ERROR_CODES)[number];

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export class BridgeError extends Error {
  readonly code: ErrorCode;
  readonly status: number | undefined;
  readonly details: Record<string, unknown> | undefined;
  readonly requestId: string | undefined;

  constructor(options: {
    code: ErrorCode;
    message: string;
    status?: number;
    details?: Record<string, unknown>;
    requestId?: string;
  }) {
    super(options.message);
    this.name = "BridgeError";
    this.code = options.code;
    this.status = options.status;
    this.details = options.details;
    this.requestId = options.requestId;
  }
}

export const isErrorCode = (value: string): value is ErrorCode =>
  (ERROR_CODES as readonly string[]).includes(value);

export const normalizeErrorCode = (value: unknown): ErrorCode => {
  if (typeof value === "string" && isErrorCode(value)) {
    return value;
  }
  return "INTERNAL_ERROR";
};

export const safeErrorMessage = (error: unknown): string => {
  if (error instanceof BridgeError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message.replace(/[A-Za-z0-9_-]{32,}/g, "[redacted]");
  }
  return "Unexpected internal failure.";
};

export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40
};

const SECRET_KEY_PATTERN = /token|authorization|secret|password|api[_-]?key/i;
const BASE64ISH_PATTERN = /^[A-Za-z0-9+/=_-]{256,}$/;

export type LogFields = Record<string, unknown>;

export interface Logger {
  debug(message: string, fields?: LogFields): void;
  info(message: string, fields?: LogFields): void;
  warn(message: string, fields?: LogFields): void;
  error(message: string, fields?: LogFields): void;
}

export const redactForLog = (value: unknown): unknown => {
  if (value === null || value === undefined) {
    return value;
  }
  if (typeof value === "string") {
    if (BASE64ISH_PATTERN.test(value)) {
      return "[redacted-large-string]";
    }
    return value.replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/g, "Bearer [redacted]");
  }
  if (typeof value !== "object") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.slice(0, 50).map((item) => redactForLog(item));
  }

  const input = value as Record<string, unknown>;
  const output: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(input)) {
    output[key] = SECRET_KEY_PATTERN.test(key) ? "[redacted]" : redactForLog(item);
  }
  return output;
};

export const createLogger = (level: LogLevel = "info"): Logger => {
  const threshold = LEVEL_ORDER[level] ?? LEVEL_ORDER.info;

  const write = (entryLevel: LogLevel, message: string, fields: LogFields = {}) => {
    if (LEVEL_ORDER[entryLevel] < threshold) {
      return;
    }
    const sanitizedFields = redactForLog(fields) as Record<string, unknown>;
    const payload = {
      timestamp: new Date().toISOString(),
      level: entryLevel,
      message,
      ...sanitizedFields
    };
    const line = JSON.stringify(payload);
    if (entryLevel === "error") {
      console.error(line);
    } else if (entryLevel === "warn") {
      console.warn(line);
    } else {
      console.log(line);
    }
  };

  return {
    debug: (message, fields) => write("debug", message, fields),
    info: (message, fields) => write("info", message, fields),
    warn: (message, fields) => write("warn", message, fields),
    error: (message, fields) => write("error", message, fields)
  };
};

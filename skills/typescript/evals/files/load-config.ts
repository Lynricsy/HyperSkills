// src/config/load-config.ts
import { readFileSync } from "node:fs";

export type LogLevel = "debug" | "info" | "warn" | "error";

export interface AppConfig {
  serviceName: string;
  port: number;
  logLevel: LogLevel;
  retries: number;
  featureFlags: Record<string, boolean>;
}

const DEFAULTS = {
  serviceName: "unnamed",
  port: 3000,
  logLevel: "info",
  retries: 3,
  featureFlags: {},
};

export function loadConfig(path: string): AppConfig {
  let raw: any;
  try {
    raw = JSON.parse(readFileSync(path, "utf8"));
  } catch (err: any) {
    if (err.code === "ENOENT") {
      return DEFAULTS as AppConfig;
    }
    throw new Error("bad config: " + err.message);
  }

  const merged = { ...DEFAULTS, ...raw } as AppConfig;

  if (merged.port < 1 || merged.port > 65535) {
    throw new Error("bad port");
  }

  for (const key of Object.keys(merged.featureFlags)) {
    const value = (merged.featureFlags as any)[key];
    if (typeof value !== "boolean") {
      throw new Error("flag " + key + " is not a boolean");
    }
  }

  return merged;
}

export function summarise(config: unknown): string {
  const c = config as AppConfig;
  return `${c.serviceName} on :${c.port} (${c.logLevel})`;
}

export async function withRetries<T>(fn: () => Promise<T>, config: AppConfig): Promise<T> {
  let lastError: any;
  for (let attempt = 0; attempt <= config.retries; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError;
}

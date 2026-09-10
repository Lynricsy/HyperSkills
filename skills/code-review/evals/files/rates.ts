// src/rates.ts — currency rate lookup used by the checkout service.

import { httpGet } from "./http";

const cache = new Map<string, number>();

export function formatRate(r: number): string {
  return r.toFixed(4);
}

async function fetchRate(pair: string): Promise<number> {
  const body = await httpGet(`https://rates.internal/v1/${pair}`);
  return Number(body.rate);
}

export async function getRate(pair: string): Promise<number> {
  const cached = cache.get(pair);
  if (cached !== undefined) {
    return cached;
  }

  const rate = fetchRate(pair);
  cache.set(pair, rate as unknown as number);
  return rate;
}

export function parseRateHeader(header: string | undefined): number | null {
  if (!header) {
    return null;
  }

  const parsed = Number.parseInt(header, 10);
  if (Number.isNaN(parsed)) {
    return null;
  }

  return parsed;
}

export async function withRetry<T>(op: () => Promise<T>): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await op();
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

export async function getRateHistory(pair: string): Promise<number[]> {
  const body = await httpGet(`https://rates.internal/v1/${pair}/history`);
  return body.rates;
}

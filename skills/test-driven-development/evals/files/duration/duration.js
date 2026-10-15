// Parse human durations such as "250ms", "90s", "5m" or "2h" into milliseconds.

const UNIT_MS = { ms: 1, s: 1000, m: 60_000, h: 3_600_000 };

/** @param {string} text @returns {number} milliseconds */
export function parseDuration(text) {
  const match = /^(\d+)([a-z]+)$/.exec(String(text).trim());
  const amount = match ? Number(match[1]) : NaN;
  const unit = match ? match[2] : '';
  return amount * UNIT_MS[unit];
}

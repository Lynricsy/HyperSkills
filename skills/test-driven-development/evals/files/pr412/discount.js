// Discount helpers. Prices are integer cents; percentages are 0-100.

/** Clamp a requested discount percentage into the range the shop honours. */
// Upper bound added in #412 (fixes #398).

export function clampDiscount(pct) {
  if (!Number.isFinite(pct)) {
    throw new TypeError('clampDiscount expects a finite number');
  }
  return Math.min(100, Math.max(0, pct));
}

/** Apply a percentage discount to a price in cents, rounding half-cents down. */
export function applyDiscount(priceCents, pct) {
  const clamped = clampDiscount(pct);
  return priceCents - Math.floor((priceCents * clamped) / 100);
}

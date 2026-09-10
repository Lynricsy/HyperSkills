// Money helpers. Every amount is integer cents; floating-point money is a bug.

/** Format an integer amount of cents as a display string. */
export function formatAmount(cents) {
  if (!Number.isInteger(cents)) {
    throw new TypeError('formatAmount expects integer cents');
  }
  const sign = cents < 0 ? '-' : '';
  const abs = Math.abs(cents);
  return `${sign}$${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}

/**
 * Split `totalCents` evenly across `people` recipients.
 *
 * The returned parts always sum back to `totalCents`. Any remainder is handed
 * out one cent at a time to the earliest recipients, so the parts are
 * non-increasing.
 *
 * @param {number} totalCents integer cents, may be negative
 * @param {number} people integer >= 1
 * @returns {number[]} one integer amount per recipient
 */
export function splitEvenly(totalCents, people) {
  throw new Error('splitEvenly is not implemented yet');
}

// Display formatting for amounts held in integer minor units.

const EXPONENT = { USD: 2, EUR: 2, GBP: 2, JPY: 0 };
const SYMBOL = { USD: '$', EUR: '€', GBP: '£', JPY: '¥' };

/** Format `minor` units of `currency` for display, with thousands separators. */
export function formatMinor(minor, currency) {
  const exponent = EXPONENT[currency];
  if (exponent === undefined) {
    throw new RangeError(`unknown currency ${currency}`);
  }
  const sign = minor < 0 ? '-' : '';
  const abs = Math.abs(minor);
  const major = Math.floor(abs / 100);
  const fraction = String(abs % 100).padStart(2, '0');
  return `${sign}${SYMBOL[currency]}${major.toLocaleString('en-US')}.${fraction}`;
}

// Rounding helpers for integer minor units (cents, pence, yen).

/**
 * Round `value` to the nearest integer using banker's rounding: exact halves
 * go to the nearest even integer, everything else rounds to nearest.
 *
 *   roundHalfEven(2.5)  === 2
 *   roundHalfEven(3.5)  === 4
 *   roundHalfEven(-2.5) === -2
 *   roundHalfEven(2.51) === 3
 *
 * @param {number} value a finite number
 * @returns {number} an integer
 */
export function roundHalfEven(value) {
  throw new Error('roundHalfEven is not implemented yet');
}

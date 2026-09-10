import { test } from 'node:test';
import assert from 'node:assert/strict';

import { formatAmount } from './money.js';

test('formatAmount renders whole dollars with two decimal places', () => {
  assert.equal(formatAmount(1200), '$12.00');
});

test('formatAmount keeps the leading zero on sub-dollar amounts', () => {
  assert.equal(formatAmount(7), '$0.07');
});

test('formatAmount puts the sign before the currency symbol', () => {
  assert.equal(formatAmount(-2599), '-$25.99');
});

test('formatAmount rejects non-integer cents', () => {
  assert.throws(() => formatAmount(12.5), TypeError);
});

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { formatMinor } from './currency.js';

test('formatMinor renders USD with two decimals and separators', () => {
  assert.equal(formatMinor(123456, 'USD'), '$1,234.56');
});

test('formatMinor puts the sign before the symbol', () => {
  assert.equal(formatMinor(-705, 'EUR'), '-€7.05');
});

test('formatMinor renders JPY without a fractional part', () => {
  assert.equal(formatMinor(1200, 'JPY'), '¥1,200');
});

test('formatMinor rejects an unknown currency', () => {
  assert.throws(() => formatMinor(100, 'XYZ'), RangeError);
});

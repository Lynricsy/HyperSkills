import { test } from 'node:test';
import assert from 'node:assert/strict';

import { applyDiscount, clampDiscount } from './discount.js';

test('applyDiscount takes 25% off 2000 cents', () => {
  assert.equal(applyDiscount(2000, 25), 1500);
});

test('applyDiscount rounds half-cents down', () => {
  assert.equal(applyDiscount(999, 50), 500);
});

test('applyDiscount leaves the price alone at 0%', () => {
  assert.equal(applyDiscount(1234, 0), 1234);
});

test('clampDiscount raises negatives to 0', () => {
  assert.equal(clampDiscount(-5), 0);
});

test('clampDiscount keeps 40 as 40', () => {
  assert.equal(clampDiscount(40), 40);
});

test('clampDiscount rejects NaN', () => {
  assert.throws(() => clampDiscount(Number.NaN), TypeError);
});

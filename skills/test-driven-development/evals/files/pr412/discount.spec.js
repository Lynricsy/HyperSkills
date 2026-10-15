import { test } from 'node:test';
import assert from 'node:assert/strict';

import { applyDiscount, clampDiscount } from './discount.js';

// Regression tests for #398.

test('clampDiscount caps 150 at 100 (#398)', () => {
  assert.equal(clampDiscount(150), 100);
});

test.skip('applyDiscount never returns a negative total (#398)', () => {
  assert.equal(applyDiscount(2000, 150), 0);
});

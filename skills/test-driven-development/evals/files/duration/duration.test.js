import { test } from 'node:test';
import assert from 'node:assert/strict';

import { parseDuration } from './duration.js';

test('parseDuration reads seconds', () => {
  assert.equal(parseDuration('90s'), 90_000);
});

test('parseDuration reads milliseconds', () => {
  assert.equal(parseDuration('250ms'), 250);
});

test('parseDuration ignores surrounding whitespace', () => {
  assert.equal(parseDuration(' 2h '), 7_200_000);
});

import { test } from 'node:test';
import assert from 'node:assert/strict';

import * as rounding from './rounding.js';

test('rounding module exports roundHalfEven', () => {
  assert.equal(typeof rounding.roundHalfEven, 'function');
});

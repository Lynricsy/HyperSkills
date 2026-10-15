import { test } from 'node:test';
import assert from 'node:assert/strict';

import { renderRunRow } from './run-row.js';

test('renderRunRow shows the first ten errors and the total', () => {
  const errors = Array.from({ length: 12 }, (_, i) => `e${i}`);
  const row = renderRunRow('r1', errors, {});
  assert.deepEqual(row.errors, ['e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9']);
  assert.equal(row.errorsTotal, 12);
});

test('renderRunRow lists only approved committees', () => {
  const row = renderRunRow('r1', [], { SEC: true, DOCS: true, PERF: false });
  assert.deepEqual(row.committees, ['SEC', 'DOCS']);
});

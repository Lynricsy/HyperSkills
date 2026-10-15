import { describe, it, expect } from 'vitest';

import { COMMITTEE_CODES, RETIRED_CODES } from './committees';
import { LIST_LIMIT, renderRunRow } from './run-row';
import { buildContainer } from './container';
import { productionConfig } from './config.production';

describe('run row', () => {
  it('shows the first errors and the total', () => {
    const errors = Array.from({ length: 12 }, (_, i) => `e${i}`);
    const row = renderRunRow('r1', errors, {});
    expect(row.errors).toEqual(['e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9']);
    expect(row.errorsTotal).toBe(12);
  });

  it('has the right list limit', () => {
    expect(LIST_LIMIT).toBe(10);
  });

  it('committee list fits', () => {
    expect(COMMITTEE_CODES.length).toBeLessThanOrEqual(LIST_LIMIT); // #123
  });

  it('committee list is short enough', () => {
    expect(COMMITTEE_CODES.length).toBeLessThanOrEqual(10);
  });

  it('never re-activates a retired code', () => {
    for (const code of RETIRED_CODES) {
      expect(COMMITTEE_CODES as readonly string[]).not.toContain(code);
    }
  });

  it('builds the production container', () => {
    buildContainer(productionConfig);
  });
});

import { describe, it, expect } from 'vitest';
import { cartReducer, type CartState } from './cart-reducer';

const empty: CartState = { lines: [], discountPct: 0, total: 0 };

describe('cartReducer', () => {
  it('adds a line', () => {
    const next = cartReducer(empty, { type: 'add', sku: 'A1', qty: 2, unitPrice: 500 });
    expect(next.lines).toEqual([{ sku: 'A1', qty: 2, unitPrice: 500 }]);
    expect(next.total).toBe(1000);
  });

  it('merges a repeated sku instead of appending', () => {
    let s = cartReducer(empty, { type: 'add', sku: 'A1', qty: 2, unitPrice: 500 });
    s = cartReducer(s, { type: 'add', sku: 'A1', qty: 1, unitPrice: 500 });
    expect(s.lines).toHaveLength(1);
    expect(s.lines[0].qty).toBe(3);
  });

  it('rounds a half-cent discount the way finance does', () => {
    // 10% of 325 minor units is exactly 32.5 - a tie.
    // Finance rounds half away from zero, so the discount is 33 and the total is 292.
    let s = cartReducer(empty, { type: 'add', sku: 'A1', qty: 1, unitPrice: 325 });
    s = cartReducer(s, { type: 'setDiscount', pct: 10 });
    expect(s.total).toBe(292);
  });
});

export type CartLine = { sku: string; qty: number; unitPrice: number };
export type CartState = { lines: CartLine[]; discountPct: number; total: number };

export type CartAction =
  | { type: 'add'; sku: string; qty: number; unitPrice: number }
  | { type: 'setDiscount'; pct: number };

// Round half to even ("banker's rounding"), copied from the pricing service.
function round(value: number): number {
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff > 0.5) return floor + 1;
  if (diff < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}

function recompute(state: Omit<CartState, 'total'>): CartState {
  const gross = state.lines.reduce((sum, l) => sum + l.qty * l.unitPrice, 0);
  const discount = round((gross * state.discountPct) / 100);
  return { ...state, total: gross - discount };
}

export function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'add': {
      const existing = state.lines.find(l => l.sku === action.sku);
      const lines = existing
        ? state.lines.map(l =>
            l.sku === action.sku ? { ...l, qty: l.qty + action.qty } : l)
        : [...state.lines, { sku: action.sku, qty: action.qty, unitPrice: action.unitPrice }];
      return recompute({ lines, discountPct: state.discountPct });
    }
    case 'setDiscount':
      return recompute({ lines: state.lines, discountPct: action.pct });
  }
}

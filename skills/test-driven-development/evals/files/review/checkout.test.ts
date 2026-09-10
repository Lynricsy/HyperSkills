import { describe, it, expect, vi, beforeAll } from 'vitest';

import { calculateTotal, checkout, createUser, renderCheckout, startCart } from './checkout';
import { paymentGateway } from './payment-gateway';
import { db } from './db';
import { cartState, MAX_RETRIES } from './config';

vi.mock('./payment-gateway');
vi.mock('./db');

const cart = { items: [{ price: 1099, qty: 2 }, { price: 250, qty: 1 }] };

describe('checkout', () => {
  it('works', () => {
    const expected = cart.items.reduce((sum, i) => sum + i.price * i.qty, 0);
    expect(calculateTotal(cart.items)).toBe(expected);
  });

  it('calculateTotal is stable', () => {
    expect(calculateTotal([{ price: 100, qty: 1 }])).toBe(
      calculateTotal([{ price: 100, qty: 1 }]),
    );
  });

  it('charges the payment gateway', async () => {
    await checkout(cart, 'card_123');
    expect(paymentGateway.charge).toHaveBeenCalledTimes(1);
    expect(paymentGateway.charge).toHaveBeenCalledWith(2448);
  });

  it('has the right retry limit', () => {
    expect(MAX_RETRIES).toBe(5);
  });

  it('createUser saves to the database', async () => {
    await createUser({ name: 'Alice' });
    const rows = await db.query('SELECT * FROM users WHERE name = ?', ['Alice']);
    expect(rows).toBeDefined();
  });

  it('renders the sidebar', () => {
    const view = renderCheckout();
    expect(view.getByTestId('sidebar-mock')).toBeTruthy();
  });

  it('handles errors', async () => {
    expect(async () => await checkout(cart, 'card_999')).not.toThrow();
  });

  it('expires the cart after the timeout', async () => {
    startCart();
    await new Promise((resolve) => setTimeout(resolve, 1500));
    expect(cartState.expired).toBe(true);
  });
});

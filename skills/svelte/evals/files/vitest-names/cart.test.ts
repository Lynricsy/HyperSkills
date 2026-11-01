// src/lib/cart.test.ts
import { expect, test } from 'vitest';
import { createCart } from './cart.svelte';

test('total follows the prices', () => {
	let prices = $state([5, 10]);
	const cart = createCart(() => prices);

	expect(cart.total).toBe(15);
	prices = [5, 10, 20];
	expect(cart.total).toBe(35);
});

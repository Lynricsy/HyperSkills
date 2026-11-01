// src/lib/server/pricing.svelte.test.ts
import { expect, test } from 'vitest';
import { priceWithTax } from './pricing';

test('adds VAT', () => {
	expect(priceWithTax(100, 0.19)).toBe(119);
});

test('rounds to cents', () => {
	expect(priceWithTax(9.99, 0.07)).toBe(10.69);
});

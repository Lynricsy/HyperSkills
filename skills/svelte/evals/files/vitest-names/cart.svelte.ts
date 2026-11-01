// src/lib/cart.svelte.ts
export function createCart(getPrices: () => number[]) {
	return {
		get total() {
			return getPrices().reduce((sum, price) => sum + price, 0);
		}
	};
}

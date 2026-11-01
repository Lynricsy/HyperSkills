// src/lib/server/pricing.ts
export function priceWithTax(net: number, rate: number) {
	return Math.round(net * (1 + rate) * 100) / 100;
}

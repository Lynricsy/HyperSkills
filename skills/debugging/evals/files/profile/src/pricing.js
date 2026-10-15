// Order pricing: integer cents throughout.

export function priceOrder(body) {
  const items = body.items.map((i) => ({ ...i, priceCents: Math.round(i.priceCents) }));
  const totalCents = items.reduce((sum, i) => sum + i.priceCents * i.qty, 0);
  return { id: body.id, currency: body.currency, items, totalCents };
}

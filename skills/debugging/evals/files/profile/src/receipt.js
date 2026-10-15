// Receipt rendering for the checkout endpoint.

/** Format integer cents in the order currency. */
export function formatMoney(cents, currency) {
  const fmt = new Intl.NumberFormat('en-US', { style: 'currency', currency });
  return fmt.format(cents / 100);
}

/** Build the printable receipt lines for an order. */
export function buildReceipt(order) {
  const lines = [];
  for (const item of order.items) {
    lines.push(`${item.name.padEnd(30)} ${formatMoney(item.priceCents * item.qty, order.currency)}`);
  }
  lines.push(`TOTAL ${formatMoney(order.totalCents, order.currency)}`);
  return lines.join('\n');
}

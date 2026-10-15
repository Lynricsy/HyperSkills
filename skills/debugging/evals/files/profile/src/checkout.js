import { buildReceipt } from './receipt.js';
import { priceOrder } from './pricing.js';

export async function handleCheckout(req, res) {
  const order = priceOrder(req.body);
  const receipt = buildReceipt(order);
  res.json({ orderId: order.id, total: order.totalCents, receipt });
}

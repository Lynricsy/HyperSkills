import { Router } from 'express';
import { orderService } from './order-service';

export const router = Router();

// GET /orders?customer=123&limit=50
router.get('/orders', async (req, res) => {
  const customer = String(req.query.customer ?? '');
  const limit = Number(req.query.limit ?? 50);
  const orders = await orderService.list({ customer, limit });
  res.json(orders);
});

router.get('/orders/:id', async (req, res) => {
  const order = await orderService.get(req.params.id);
  if (!order) {
    res.status(404).json({ error: 'not found' });
    return;
  }
  res.json(order);
});

router.post('/orders', async (req, res) => {
  try {
    const order = await orderService.place(req.body);
    res.status(200).json(order);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

router.post('/orders/:id/cancel', async (req, res) => {
  try {
    await orderService.cancel(req.params.id);
    res.json({ ok: true });
  } catch (err) {
    res.status(400).json({ error: String(err) });
  }
});

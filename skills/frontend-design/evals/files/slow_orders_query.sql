-- Reporting query behind the internal ops dashboard.
-- Runs on PostgreSQL 16. Currently ~14s on a 40M-row orders table.
SELECT
  c.id                                   AS customer_id,
  c.email,
  COUNT(o.id)                            AS order_count,
  SUM(oi.quantity * oi.unit_price_cents)  AS lifetime_cents,
  MAX(o.placed_at)                       AS last_order_at
FROM customers c
LEFT JOIN orders o
  ON o.customer_id = c.id
LEFT JOIN order_items oi
  ON oi.order_id = o.id
WHERE o.placed_at >= NOW() - INTERVAL '18 months'
  AND LOWER(c.email) LIKE '%@example.com'
  AND o.status NOT IN (
    SELECT status FROM order_statuses WHERE is_cancelled
  )
GROUP BY c.id, c.email
HAVING COUNT(o.id) > 2
ORDER BY lifetime_cents DESC
LIMIT 500;

-- Existing indexes:
--   orders_pkey (id)
--   order_items_pkey (id)
--   customers_pkey (id)
--   idx_orders_customer_id (customer_id)

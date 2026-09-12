SELECT c.region, COUNT(DISTINCT o.order_id) AS orders,
       SUM(o.gross_usd)-COALESCE(SUM(r.refund_usd),0) AS net_usd
FROM read_csv('orders.csv') o
JOIN read_csv('order_lines.csv') l USING(order_id)
LEFT JOIN read_csv('refunds.csv') r USING(order_id)
LEFT JOIN read_csv('customers.csv') c USING(customer_id)
GROUP BY c.region;

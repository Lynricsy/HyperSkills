-- Postgres 18.6, orders table is 41M rows and growing ~2M/month.
-- This query backs the merchant "unfulfilled orders" screen and takes 6-9s.

SELECT o.id, o.created_at, o.total_cents, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.merchant_id = 8812
  AND o.status = 'unfulfilled'
ORDER BY o.created_at DESC
LIMIT 50;

-- \d+ orders (abridged)
--  id            bigint       not null
--  merchant_id   bigint       not null
--  customer_id   bigint       not null
--  status        text         not null
--  total_cents   bigint       not null
--  created_at    timestamptz  not null
-- Indexes:
--   "orders_pkey" PRIMARY KEY, btree (id)
--   "orders_created_at_idx" btree (created_at DESC)
--   "orders_status_idx" btree (status)

-- EXPLAIN (ANALYZE, BUFFERS)
--
-- Limit  (cost=0.00..812441.02 rows=50 width=48) (actual time=7211.884..7213.006 rows=50 loops=1)
--   Buffers: shared hit=1204 read=418337
--   ->  Nested Loop  (cost=0.00..8912773.51 rows=548 width=48) (actual time=7211.882..7212.991 rows=50 loops=1)
--         Buffers: shared hit=1204 read=418337
--         ->  Index Scan Backward using orders_created_at_idx on orders o
--               (cost=0.43..8901120.28 rows=548 width=32)
--               (actual time=7211.774..7212.402 rows=50 loops=1)
--               Filter: ((merchant_id = 8812) AND (status = 'unfulfilled'::text))
--               Rows Removed by Filter: 3918442
--               Buffers: shared hit=1102 read=418291
--         ->  Index Scan using customers_pkey on customers c
--               (cost=0.42..2.12 rows=1 width=24)
--               (actual time=0.010..0.010 rows=1 loops=50)
--               Index Cond: (id = o.customer_id)
--               Buffers: shared hit=102 read=46
-- Planning Time: 0.214 ms
-- Execution Time: 7213.061 ms

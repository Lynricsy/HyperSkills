-- Reporting database, PostgreSQL 18.6. The `events` table has ~500k rows today
-- and grows by roughly 2M rows a month.

CREATE TABLE events (
    id          bigserial PRIMARY KEY,
    tenant_id   integer     NOT NULL,
    created_at  timestamptz NOT NULL,
    status      text        NOT NULL,   -- 'ok' | 'failed' | 'retrying'
    payload     text
);

-- Indexes that exist today
CREATE INDEX events_created_tenant ON events (created_at DESC, tenant_id);
CREATE INDEX events_status         ON events (status);
CREATE INDEX events_tenant         ON events (tenant_id);

-- ---------------------------------------------------------------------------
-- Query 1 -- the tenant dashboard. Used to be instant, now takes ~300ms and is
-- getting slower every week. Roughly 50 tenants; a handful of them (the ones
-- that complain) have only a few hundred rows each.

SELECT count(*) FROM events WHERE tenant_id = 999;

--                                  QUERY PLAN
-- ------------------------------------------------------------------------------
--  Finalize Aggregate (actual rows=1.00 loops=1)
--    Buffers: shared hit=6668
--    ->  Gather (actual rows=3.00 loops=1)
--          Workers Planned: 2
--          Workers Launched: 2
--          Buffers: shared hit=6668
--          ->  Partial Aggregate (actual rows=1.00 loops=3)
--                Buffers: shared hit=6668
--                ->  Parallel Seq Scan on events (actual rows=33.33 loops=3)
--                      Filter: (tenant_id = 999)
--                      Rows Removed by Filter: 166667
--                      Buffers: shared hit=6668

-- ---------------------------------------------------------------------------
-- Query 2 -- the failure feed. `status = 'failed'` is about 5% of rows.

SELECT count(*) FROM events WHERE tenant_id = 7 AND status = 'failed';

--                                   QUERY PLAN
-- ---------------------------------------------------------------------------------
--  Aggregate (actual rows=1.00 loops=1)
--    Buffers: shared read=36
--    ->  Bitmap Heap Scan on events (actual rows=0.00 loops=1)
--          Recheck Cond: ((tenant_id = 7) AND (status = 'failed'::text))
--          Buffers: shared read=36
--          ->  BitmapAnd (actual rows=0.00 loops=1)
--                Buffers: shared read=36
--                ->  Bitmap Index Scan on events_tenant (actual rows=10000.00 loops=1)
--                      Index Cond: (tenant_id = 7)
--                      Buffers: shared read=12
--                ->  Bitmap Index Scan on events_status (actual rows=25000.00 loops=1)
--                      Index Cond: (status = 'failed'::text)
--                      Buffers: shared read=24

-- ---------------------------------------------------------------------------
-- Query 3 -- the paginated tenant timeline the UI actually calls.

SELECT * FROM events
WHERE tenant_id = $1
ORDER BY created_at DESC
LIMIT 20 OFFSET $2;   -- $2 goes up to 40000 on the "load more" path

# askdesk retrieval database — index notes

Postgres 16.4, `pgvector` 0.8.0. One table.

```sql
CREATE TABLE handbook (
  path      text PRIMARY KEY,
  body      text NOT NULL,
  embedding vector(1536)
);

CREATE INDEX handbook_embedding_idx
  ON handbook USING hnsw (embedding vector_cosine_ops);
```

- 1 180 000 rows after the chunking change.
- `SET hnsw.ef_search` is never set; whatever the default is, that is what we get.
- The index was built before the bulk load, with default
  `m` / `ef_construction`.
- `maintenance_work_mem` is 64 MB on this instance; `shared_buffers` is 2 GB;
  the instance has 16 GB of RAM.
- `EXPLAIN ANALYZE` on the nearest-neighbour query:

```
Limit  (cost=0.00..4321.88 rows=8 width=64) (actual time=2841.203..2841.219 rows=8 loops=1)
  ->  Index Scan using handbook_embedding_idx on handbook
        (cost=0.00..640000.00 rows=1180000 width=64)
        (actual time=2841.200..2841.213 rows=8 loops=1)
        Order By: (embedding <=> '[...]'::vector)
Planning Time: 0.214 ms
Execution Time: 2841.402 ms
```

- `pg_stat_progress_create_index` showed the last rebuild spilling to disk.
- Recall was measured against exact search: 0.61 at the current settings.
- p95 latency budget for the retrieval call is 150 ms. We are at 2.8 s.

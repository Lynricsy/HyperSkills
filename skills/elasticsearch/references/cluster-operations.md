# Cluster sizing, allocation and security

Verified against: Elasticsearch 9.5.3. Not applicable to Elastic Cloud Serverless, where shards,
nodes and allocation are managed internally and these APIs are absent.

## Contents

- [Shard count comes from data volume](#shard-count-comes-from-data-volume)
- [Heap](#heap)
- [Node roles](#node-roles)
- [Allocation and why a shard will not move](#allocation-and-why-a-shard-will-not-move)
- [Disk watermarks](#disk-watermarks)
- [Thread pools and rejections](#thread-pools-and-rejections)
- [Circuit breakers](#circuit-breakers)
- [Refresh, flush, merge](#refresh-flush-merge)
- [Rolling restarts and upgrades](#rolling-restarts-and-upgrades)
- [Security](#security)

## Shard count comes from data volume

```
primary_shards = max(1, ceil(expected_primary_gb / target_shard_size_gb))
```

`target_shard_size_gb` is 10–30 for search-latency-sensitive workloads and 30–50 for logs, where
throughput and retention matter more than per-query latency. 210 GB/day of logs at a 40 GB target
is 5 primaries. Not "one per node", not "3 because that is the default in the tutorial".

- Primary count is fixed at index creation. `_shrink` and `_split` exist but both write a whole new
  index, so they are a reindex with extra steps.
- Too few shards: a ceiling on query parallelism, slow recovery, and eventually a shard too large
  to relocate.
- Too many shards: every shard is a full Lucene index with fixed heap and file-handle overhead.
  Budget **20 shards per GB of heap** as a soft ceiling — 31 GB of heap is about 620 shards per
  node. The hard stop is `cluster.max_shards_per_node` (default 1000, replicas counted), past which
  the cluster refuses to create indices at all.
- Total shards = `indices × primaries × (1 + replicas)`. Replicas count against every budget above.
- Data that keeps growing gets rollover, not a bigger guess. See `data-lifecycle.md`.

Replicas: 1 is the default and the right answer for anything whose loss would matter. 0 is correct
for a single-node development cluster (which otherwise sits yellow forever) and during a
rebuildable bulk load. More than 1 buys read throughput at a linear storage cost.

## Heap

```
Xms = Xmx = min(RAM / 2, 31g)
```

- The other half of the RAM is the OS page cache, which is what Lucene actually reads from.
  Starving it costs more than the extra heap gains.
- Above roughly 32 GB the JVM drops compressed ordinary object pointers, so 33 GB of heap addresses
  *fewer* objects than 31 GB. Confirm rather than assume: the startup log prints
  `compressed ordinary object pointers [true]`.
- A 64 GB machine therefore gets 31 GB, not 48 GB. Two Elasticsearch nodes on one big machine is a
  legitimate way to use more of it, with `cluster.routing.allocation.same_shard.host: true` so a
  primary and its replica never land on the same physical host.
- `Xms` must equal `Xmx` so the JVM does not resize the heap under load.
- Persistent high heap with frequent old-generation GC is usually fielddata, too many shards, or
  aggregation buckets — not a reason to raise the heap.

## Node roles

| Role | Holds | Scale with |
|---|---|---|
| `master` | Cluster state | Always 3 dedicated masters in production; `discovery.type: single-node` only for development |
| `data_hot` / `data_content` | Recent and searchable data | Indexing and query volume |
| `data_warm` / `data_cold` / `data_frozen` | Ageing data, progressively cheaper storage | Retention |
| `ingest` | Ingest pipelines | Pipeline CPU |
| `ml` | Model deployment (needed by `semantic_text`, ELSER, reranking) | Inference load |
| `remote_cluster_client` | Cross-cluster search | — |

Three dedicated master nodes is not superstition: with two, any split loses quorum, and with
masters that also hold data, a heavy aggregation can stall cluster-state publication and trigger a
false failover.

## Allocation and why a shard will not move

`POST /_cluster/allocation/explain` (empty body picks an unassigned shard for you) answers this,
and the answer is in a specific field. Read in this order:

1. `primary` — `false` is an unassigned replica (yellow, no data loss); `true` is an unassigned
   primary (red, that shard's data is unavailable).
2. `can_allocate` — `no`, `yes`, `throttled`, `no_valid_shard_copy`.
3. `unassigned_info.reason` — what *triggered* it (`NODE_LEFT`, `INDEX_CREATED`,
   `ALLOCATION_FAILED`). **This is not the root cause** when `can_allocate` is `no`.
4. `node_allocation_decisions[].deciders[]` — find the decider with `decision: "NO"`. The decider
   name is the cause class.

| Decider / verdict | Cause | Fix |
|---|---|---|
| `disk_threshold` NO | A candidate node is above the high watermark | Free disk, add capacity, or move shards; see below |
| `filter` / `awareness` NO | `index.routing.allocation.*` or zone awareness has nowhere to put it | Add a node matching the attributes, or relax the rule |
| `throttling` | Recovery already in flight | Wait; watch `GET /_cat/recovery` |
| `same_shard` NO | The only candidate already holds another copy | Add a node |
| `no_valid_shard_copy` | Every copy is gone | Bring the node back, or restore from snapshot. `allocate_empty_primary` is a last resort that **permanently discards that shard's documents** |
| `can_allocate: yes`, still unassigned | Delayed allocation timer, or cluster state catching up | Check `unassigned_info.at`, wait |

Yellow on a single-node cluster is expected, not a fault: measured on 9.5.3, creating an index
gives `status: yellow` with the replica `UNASSIGNED / INDEX_CREATED` because there is nowhere else
to put it. Set `number_of_replicas: 0` for development.

## Disk watermarks

| Watermark | Default | Behaviour |
|---|---|---|
| `low` | 85% | No new shards allocated to that node |
| `high` | 90% | Existing shards are relocated away |
| `flood_stage` | 95% | Every index with a shard on that node is set read-only (`index.blocks.read_only_allow_delete`) |

The flood-stage block is the one that produces "the whole cluster suddenly rejects writes". It
clears automatically once usage drops below the high watermark. Raising the watermarks buys hours,
not a fix, and leaves less room for the merges that would reclaim space.

`GET /_cat/allocation?v` shows per-node disk usage; `GET /_cat/indices?v&s=store.size:desc` shows
where the space went.

## Thread pools and rejections

`GET /_cat/thread_pool/search,write,get?v&h=node_name,name,active,queue,rejected`

- `rejected` is **cumulative since node start**, not a rate. Two samples a minute apart, or it
  means nothing. A cluster up for a year with 18 000 rejections may be perfectly healthy.
- Search pool size is derived from processor count and is not usefully tunable; a full queue means
  too many concurrent searches or searches that are too expensive.
- `es_rejected_execution_exception` on the write pool means the bulk pipeline found its ceiling.
  Back off and reduce concurrency. Retrying immediately makes it worse.

`GET /_nodes/hot_threads` is what a pegged node is actually executing; take it two or three times
and look for the stack that keeps appearing.

## Circuit breakers

| Breaker | Default | Guards |
|---|---|---|
| `indices.breaker.request` | 60% of heap | One request's aggregation memory |
| `indices.breaker.fielddata` | 40% of heap | Fielddata on `text` fields |
| `network.breaker.inflight_requests` | 100% of heap | Request bodies in flight |
| `indices.breaker.total` | 95% of real memory | Everything |

`circuit_breaking_exception` means a request asked for more heap than it is allowed. Narrow the
request: smaller aggregation `size`, `composite` pagination, smaller bulk batches, fewer
`docvalue_fields`. Raising a breaker converts a rejected query into a dead node, and a dead node
converts a yellow cluster into a red one.

## Refresh, flush, merge

- **Refresh** makes recent writes visible by opening a new segment. Default `index.refresh_interval`
  is 1s; raising it to 30s on a log index is one of the cheapest indexing-throughput wins there is.
  `?refresh=wait_for` on a write blocks until the next refresh; `?refresh=true` forces one and is
  the wrong default in application code.
- **Flush** writes the Lucene commit point and trims the translog. Elasticsearch handles it; the
  knobs (`index.translog.*`) trade durability for throughput and `async` durability means
  acknowledged writes can be lost on a crash.
- **Merge** consolidates segments in the background and is I/O bound. Many tiny segments (from a
  low refresh interval under heavy write) means merge pressure. `_forcemerge?max_num_segments=1` is
  for indices that will never be written again — on a live index it competes with everything and
  produces one huge segment that never merges away.

## Rolling restarts and upgrades

1. `PUT /_cluster/settings` with `persistent.cluster.routing.allocation.enable: "primaries"` so the
   cluster does not start copying replicas the moment the node leaves.
2. Optionally `POST /_flush` to shorten recovery.
3. Restart the node, wait for it to rejoin (`GET /_cat/nodes`).
4. Re-enable allocation (`"enable": null`) and wait for green before touching the next node.

Version rules: an index created by major version *N-1* can be read by *N* but not by *N+1*.
Measured on 9.5.3, `GET /` reports `minimum_wire_compatibility_version: 8.19.0` and
`minimum_index_compatibility_version: 8.0.0`. So the upgrade path from 7.x to 9.x goes through
8.x, and 7.x-created indices must be reindexed (or archived) before the 9.x upgrade — check with
the deprecation info API before starting, not during.

## Security

- Security is on by default in 8.x and later. A cluster with `xpack.security.enabled: false` is a
  development cluster; do not carry that setting into production, and never expose 9200 directly.
- **API keys, not user passwords, for applications.** `POST /_security/api_key` with
  `role_descriptors` scoping the key to the indices and privileges it needs, plus an `expiration`.
  A key is revocable on its own without touching any user.
- Least privilege in practice: an ingest key gets `create_doc` on one index pattern; a search key
  gets `read` on one alias. `all` on `*` is the default in most tutorials and belongs nowhere.
- Document- and field-level security (`query` and `field_security` in a role) is a Platinum
  feature. On lower tiers, isolate tenants with separate indices plus an alias filter, and treat
  the alias filter as a routing convenience rather than a security boundary — a client that can
  name the underlying index bypasses it.
- TLS on both the HTTP and transport layers; certificate verification on. Transport TLS is what
  stops an unauthenticated node from joining the cluster.
- Never interpolate user input into `query_string`, script sources or ES|QL text. Use
  `simple_query_string` for user-supplied operator syntax, and parameters (`params` in Painless,
  `?` placeholders in ES|QL) everywhere else.
- Audit logging is a paid tier. On basic, the slow log plus the proxy in front of Elasticsearch are
  what you have.

<!-- sources: clawic-elasticsearch, elastic-agent-skills, elastic-docs, elasticsearch-repo -->

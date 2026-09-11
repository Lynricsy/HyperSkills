# Data streams, lifecycle and reindexing

Verified against: Elasticsearch 9.5.3.

## Contents

- [Aliases first](#aliases-first)
- [Data streams](#data-streams)
- [Rollover](#rollover)
- [Lifecycle: ILM and the data-stream lifecycle](#lifecycle-ilm-and-the-data-stream-lifecycle)
- [Index modes: standard, logsdb, time_series, lookup](#index-modes-standard-logsdb-time_series-lookup)
- [Reindexing without downtime](#reindexing-without-downtime)
- [Bulk indexing](#bulk-indexing)
- [Ingest pipelines](#ingest-pipelines)
- [Snapshots](#snapshots)

## Aliases first

Every index that matters is created behind an alias, on day one. The reason is arithmetic: a
mapping change requires a new index, a new index requires a cutover, and a cutover through an
alias is one atomic API call while a cutover through application configuration is a deploy.

```json
POST /_aliases
{ "actions": [ { "remove": { "index": "events-000001", "alias": "events" } },
               { "add":    { "index": "events-000002", "alias": "events" } } ] }
```

Both actions apply in one cluster-state update, so no request sees both indices or neither. An
alias pointing at several indices needs exactly one of them marked `is_write_index: true` before it
can accept writes. A `filter` on an alias makes it a saved view; `routing` on an alias pins its
requests to one shard.

## Data streams

A data stream is an alias with rollover built in, for append-only time-based data. Writes go to the
stream name; Elasticsearch routes them to the current backing index (`.ds-<name>-<date>-NNNNNN`).

Create one by giving an index template a `data_stream: {}` block:

```json
PUT /_index_template/logs-app
{ "index_patterns": ["logs-app-*"], "data_stream": {},
  "template": { "mappings": { "properties": { "@timestamp": { "type": "date" } } } } }
```

Constraints that catch people out, both measured on 9.5.3:

- The mapping must have an `@timestamp` `date` (or `date_nanos`) field.
- **Only `create` operations are allowed.** `PUT /{stream}/_doc/{id}` returns
  `only write ops with an op_type of create are allowed in data streams`. Updating or deleting a
  specific document requires targeting the backing index by name, or `_update_by_query` /
  `_delete_by_query` against the stream.

Use a data stream for logs, metrics, traces, events and audit trails. Do not use one for anything
that gets updated in place — a product catalogue is an ordinary index behind an alias.

Hand-rolled `logs-YYYY.MM.DD` indices created by a cron job are the pattern data streams replace.
They fail in exactly one way: the job does not run, and writes silently continue into yesterday's
index, so the failure is invisible until someone queries a date range.

## Rollover

Rollover ends the current backing index and starts a new one. Conditions are evaluated on the
write index and are OR-ed:

| Condition | Typical value | Why |
|---|---|---|
| `max_primary_shard_size` | `40gb` | The one that actually keeps shard size right; prefer it over `max_size` |
| `max_age` | `7d`–`30d` | Bounds how long a deletion waits for the whole index to age out |
| `max_primary_shard_docs` | `200000000` | Guards the Lucene per-shard document ceiling |

`min_*` conditions (`min_docs: 1`) prevent rolling over an empty index when only `max_age` is
configured — otherwise a quiet stream accumulates empty backing indices.

Manual rollover (`POST /{stream}/_rollover`) exists for cutting over after a mapping change: new
fields land in the new backing index, old data stays readable in the old ones. That is the only
mapping change a time-based stream needs — no reindex, as long as the change is additive.

## Lifecycle: ILM and the data-stream lifecycle

Two mechanisms:

- **ILM** (`PUT /_ilm/policy/...`) — the full state machine over hot / warm / cold / frozen /
  delete phases, with `rollover`, `shrink`, `forcemerge`, `searchable_snapshot`, `allocate` and
  `delete` actions. Needed whenever there are tiers, searchable snapshots or shrink.
- **Data-stream lifecycle** (`lifecycle: { data_retention: "30d" }` in the template) — retention
  and automatic rollover only, no tiers, no separate policy object. Enough for most single-tier
  deployments and much harder to get wrong.

Rules that save outages:

- Phase timings are relative to **rollover**, not to document timestamps. A `warm` phase at
  `min_age: 7d` starts 7 days after the index stopped being written, not 7 days after the events
  in it happened.
- `forcemerge` rewrites every segment. Run it only in a phase where the index is read-only and
  never on a hot index — it competes with indexing for I/O and cannot be cancelled cleanly.
- `shrink` requires all primaries on one node and a shard count that divides the original.
- `GET /{index}/_ilm/explain` is where a stuck index tells you which action failed and why. An ILM
  policy that errored stays errored until `POST /{index}/_ilm/retry`.
- Changing a policy applies to indices already using it, at their next phase transition. Changing
  the template's policy reference applies only to indices created afterwards.

## Index modes: standard, logsdb, time_series, lookup

`index.mode` is set at creation and changes defaults wholesale.

| Mode | For | What changes |
|---|---|---|
| `standard` | Everything else | — |
| `logsdb` | Log data | Synthetic `_source`, and `index.sort.field` defaults to `["@timestamp"]` (measured). Large storage saving, and `_source` is reconstructed rather than stored |
| `time_series` | Metrics | Requires `time_series_dimension` fields, routes by dimension hash, enables downsampling and the `TS` ES\|QL command |
| `lookup` | Small dimension tables | Single shard, replicated to every node; required as the target of `LOOKUP JOIN` |

Synthetic `_source` (in `logsdb` and `time_series`) is not a free storage win: the document you get
back is reconstructed from doc_values, so field order, whitespace, and duplicate array entries are
not preserved and arrays come back sorted and deduplicated. Anything that round-trips documents
through Elasticsearch needs to tolerate that.

## Reindexing without downtime

```
new index (corrected mapping)  →  _reindex  →  verify  →  alias swap  →  drop old
```

1. Create the destination with the full corrected mapping and settings. For a big reindex set
   `number_of_replicas: 0` and `refresh_interval: -1` on the destination and restore both after.
2. `POST /_reindex` with `wait_for_completion=false`; keep the task id and poll
   `GET /_tasks/{id}`. Add `"slices": "auto"` to parallelise by source shard.
3. Transform on the way through with `"script"` (a Painless `ctx._source` rewrite) or a
   destination `pipeline` — an ingest pipeline is easier to test and easier to reuse.
4. Handle the writes that arrive during the copy: either write to both indices from the
   application, or reindex a second time with a `range` query on the timestamp to catch the delta,
   then swap.
5. Verify with `GET /{index}/_count` on both sides and a spot-check of `_mapping`, then swap the
   alias, then delete the old index — in that order, and not on the same day if you can help it.
6. `_reindex` continues on version conflicts only if you set `"conflicts": "proceed"`; the default
   aborts, leaving a partial copy. Read the task's `failures` array before believing a reindex
   succeeded.

`_reindex` is throttled with `requests_per_second` and can be re-throttled while running
(`POST /_reindex/{task}/_rethrottle`). A reindex that saturates I/O will slow live search on the
same nodes.

## Bulk indexing

- Batch by payload size, not document count. Start around 5–15 MB per `_bulk` request with a few in
  flight, raise until throughput flattens or `es_rejected_execution_exception` appears. That
  rejection is the signal that the ceiling was found — retry with backoff and lower concurrency,
  not harder.
- **A `_bulk` request returns HTTP 200 while individual items fail.** Branch on the response's
  `errors` boolean and inspect per-item `status` every single time, or documents disappear quietly.
- For a rebuildable load: `refresh_interval: -1` and `number_of_replicas: 0` during the load, then
  restore both. Every refresh seals a segment, so a four-hour load at the default one-second
  refresh creates roughly 14 000 tiny segments that merging then has to grind back down. Adding
  replicas afterwards copies finished segments instead of re-indexing every document. The escape
  hatch: keep replicas if the source cannot be replayed, because until they are back there is no
  redundancy.
- Let Elasticsearch generate `_id` when you can. A supplied `_id` forces a lookup to check whether
  the document already exists; an auto-generated one skips it.
- Concurrency control: `retry_on_conflict` for `_update`, and `if_seq_no` + `if_primary_term` for
  read-modify-write. `version_conflict_engine_exception` means another writer got there first.

## Ingest pipelines

An ingest pipeline runs processors on the coordinating (or ingest-role) node before indexing:
`set`, `rename`, `convert`, `grok`, `dissect`, `date`, `script`, `enrich`, `remove`.

- Attach it with `index.default_pipeline` (runs for every write) or `index.final_pipeline` (runs
  last, after any pipeline the request named) rather than making every client remember it.
- `POST /_ingest/pipeline/{id}/_simulate` with sample documents is the test. Write it before the
  pipeline goes near real data; a `grok` pattern that fails puts the error in the document's
  `_ingest` metadata rather than rejecting the write.
- `on_failure` handlers at pipeline or processor level are what turn a parse failure into a tagged
  document instead of a rejected one.
- Heavy pipelines consume CPU on ingest nodes. Parsing that could be done at the producer usually
  should be.

## Snapshots

- A snapshot repository (`PUT /_snapshot/{repo}`) is shared storage every node can reach —
  filesystem, S3, GCS, Azure. Registering it on some nodes only produces failures that look random.
- Snapshots are incremental at the segment level, so a daily snapshot of a mostly-static index is
  cheap; a daily `forcemerge` makes every snapshot afterwards full-size.
- SLM (`PUT /_slm/policy/...`) schedules them and applies a retention policy. A snapshot policy
  with no retention fills the repository.
- **A snapshot you have not restored is a hypothesis.** Restore into a differently-named index on a
  test cluster on a schedule, and check document counts. `GET /_snapshot/{repo}/{snap}/_status` is
  progress, not verification.
- Restore cannot overwrite an open index: close it first, or restore with `rename_pattern` /
  `rename_replacement` into a new name and swap the alias.

<!-- sources: elastic-agent-skills, clawic-elasticsearch, elastic-docs -->

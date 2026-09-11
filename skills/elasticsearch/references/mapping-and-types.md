# Mapping and field types

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1), basic licence, single node.

## Contents

- [Pick the type from the access pattern](#pick-the-type-from-the-access-pattern)
- [What dynamic mapping actually produces](#what-dynamic-mapping-actually-produces)
- [text, keyword and multi-fields](#text-keyword-and-multi-fields)
- [Objects, arrays and nested](#objects-arrays-and-nested)
- [flattened for unbounded key spaces](#flattened-for-unbounded-key-spaces)
- [Storage switches: doc_values, index, store, _source](#storage-switches-doc_values-index-store-_source)
- [Runtime fields: schema on read](#runtime-fields-schema-on-read)
- [The hard limits and their error strings](#the-hard-limits-and-their-error-strings)
- [Index templates and component templates](#index-templates-and-component-templates)
- [Changing a mapping that already exists](#changing-a-mapping-that-already-exists)

## Pick the type from the access pattern

Ask, per field: searched as prose, filtered exactly, aggregated, sorted, or only returned?
Everything else follows.

| Access pattern | Type |
|---|---|
| Full-text search only | `text` |
| Exact filter / terms aggregation / sort | `keyword` |
| Both, on one logical field | `text` with a `keyword` sub-field |
| Returned in hits, never queried | `keyword` with `doc_values: false` (or `index: false`) |
| Decimal metric with bounded precision | `scaled_float` + `scaling_factor` |
| Decimal metric, unbounded | `double` (`float` loses cents on large amounts) |
| Integral identifier that is never range-queried | `keyword`, not `long` — `keyword` is faster for term lookups |
| Free-form key/value with unbounded keys | `flattened` |
| Array of objects whose fields must stay associated per item | `nested` |
| Timestamp | `date` (or `date_nanos` when sub-millisecond ordering matters) |
| IP address | `ip` — supports CIDR range queries, a `keyword` does not |
| Version string | `version` — sorts semver correctly, `keyword` sorts `1.10` before `1.9` |
| Value derived from others, needed at query time | runtime field, or a `keyword`/numeric written by an ingest pipeline |

Missing access-pattern information is a blocker, not something to guess: the wrong type is only
fixable by reindexing the whole index.

## What dynamic mapping actually produces

With `"dynamic": true` (the default) the first document decides. Measured on 9.5.3, indexing
`{"title":"Quick Brown Fox","price":9.99,"ts":"2026-09-11T00:00:00Z"}` into an empty index gives:

```json
{
  "title": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
  "price": { "type": "float" },
  "ts":    { "type": "date" }
}
```

Three consequences people trip over:

- Every string costs two indexed forms, whether or not both are used.
- Floating-point JSON becomes `float`, not `double` — enough precision loss to matter for money.
- A numeric that arrived quoted (`"status_code": "503"`) becomes `text`+`keyword`, and stays that
  way for the life of the index even after the producer is fixed.

`"dynamic": "strict"` rejects unknown fields with `strict_dynamic_mapping_exception` at index
time. Prefer it for anything user-facing: a typo in a field name is otherwise silently created
with a guessed type and the documents that used the correct name stop matching.
`"dynamic": "runtime"` is the middle setting — new fields become runtime fields, queryable but
not indexed, so a mapping mistake costs query time rather than disk.

## text, keyword and multi-fields

`text` is analysed into tokens at index time; `keyword` is stored verbatim. A `term` query is not
analysed. That mismatch produces the single most common bug report in Elasticsearch: a `term`
query against a `text` field returns HTTP 200 with zero hits and no error at all. Run
`POST /{index}/_analyze` with `{"field": "...", "text": "..."}` and compare the tokens to the
value you are searching for before believing the data is missing.

The multi-field is the answer when one logical field is both searched and faceted:

```json
{ "name": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } } }
```

Search `name`, aggregate and sort on `name.keyword`. Two rules around it:

- `ignore_above` is not decoration. Without it a `keyword` sub-field on a long log line indexes the
  entire string as one term — useless as an aggregation key, and a real per-document cost. A value
  longer than `ignore_above` is not indexed at all for that sub-field (it stays in `_source`, so it
  still comes back in hits, and it silently never matches a `term`).
- Do not add the sub-field out of habit. A field that is only ever full-text searched should be
  plain `text`; a field that is only ever filtered should be plain `keyword`.

`keyword` is case-sensitive and unanalysed, so `"Active"` and `"active"` are different terms. Use a
`normalizer` (a keyword-only analysis chain, typically `lowercase`) rather than lower-casing in the
application, because the normalizer applies to the query term too.

## Objects, arrays and nested

An `object` field containing an array of objects is flattened into parallel arrays, and the
per-item association is lost. Measured: with `users` mapped as `object` and the document
`{"users":[{"first":"Alice","last":"Smith"},{"first":"Bob","last":"Jones"}]}`, a filter of
`users.first: Alice` **and** `users.last: Jones` matches the document. There is no Alice Jones.

`nested` indexes each array element as a hidden separate document so the association survives, at
three costs: writes fan out (updating one element reindexes the whole parent), queries must be
wrapped in a `nested` query with a `path`, and aggregations over them need a `nested` aggregation.
Defaults cap the damage: `index.mapping.nested_fields.limit` is 100 nested field definitions per
index and `index.mapping.nested_objects.limit` is 10 000 nested documents per parent document.

Use `nested` only when a query really must combine two fields of the same array element. If items
are only ever filtered one field at a time, plain `object` is cheaper and correct.

`join` (parent-child) is the escape hatch for the case where children are updated far more often
than parents and cannot be reindexed with them. It costs a query-time join and confines both sides
to the same shard; reach for it only after `nested` has been ruled out.

## flattened for unbounded key spaces

A `flattened` field indexes an entire JSON object as a set of `keyword` values under one mapped
field. Kubernetes labels, HTTP headers, per-customer attribute bags and A/B experiment buckets all
belong here: with a dynamic `object` each new key becomes a new mapped field, the mapping grows
without bound, and the cluster state grows with it until indexing fails with
`Limit of total fields [1000] has been exceeded`.

What you give up: everything under a `flattened` field is a `keyword`. No full-text search, no
numeric ranges, no per-key analysis. Filter with `labels.deploy_sha: "3f21ab9"`, aggregate on
`labels.k8s_pod_name`, and promote the two or three keys that need real types to proper top-level
fields (via an ingest pipeline) instead of trying to make `flattened` do it.

`index.mapping.total_fields.ignore_dynamic_beyond_limit` (default `false`) is the blunt alternative:
it makes documents beyond the limit index anyway with the extra fields marked `_ignored` rather than
rejected. That converts a loud failure into silent data loss; use it only as a stopgap while the
real fix ships.

## Storage switches: doc_values, index, store, _source

| Switch | Default | Turn it off when | Cost of being wrong |
|---|---|---|---|
| `index` | `true` | The field is never searched or filtered | Cannot query the field at all |
| `doc_values` | `true` (not on `text`) | Never aggregated, sorted, or used in scripts | Aggregation and sort fail on that field |
| `norms` | `true` on `text` | Field length should not affect scoring (tags, codes) | Scoring changes; cannot be re-enabled without reindex |
| `store` | `false` | — | Rarely useful; `_source` filtering is normally cheaper |

`_source` itself has a mode: `index.mapping.source.mode` is `STORED` by default and `SYNTHETIC` in
`logsdb` and `time_series` index modes. Synthetic `_source` reconstructs the document from
doc_values instead of storing the original JSON, which is a large storage win and changes what you
get back: field order, whitespace and duplicate array values are not preserved, and arrays come
back sorted and deduplicated.

Vectors are a special case in 9.x. `index.mapping.exclude_source_vectors` defaults to `true`, so a
`dense_vector` value does **not** come back in `_source`. Measured: after indexing
`{"emb":[0.1,0.2,0.3],"txt":"alpha"}`, `GET /{index}/_doc/1` returns only `txt`. Code that reads the
embedding back out of a hit gets nothing and no error.

## Runtime fields: schema on read

A runtime field is defined in the mapping (or per search, under `runtime_mappings`) and evaluated
at query time from `_source` or from other doc_values. It costs query time and saves a reindex.

```json
{
  "runtime_mappings": {
    "title_len": { "type": "long", "script": { "source": "emit(params._source.title.length())" } }
  },
  "fields": ["title_len"]
}
```

Use it for: fixing a wrong type without reindexing yet, exposing a value the producer forgot to
send, and exploring a field before committing to a mapping. Do not use it for a field that is
filtered on every request across a large index — a runtime field is evaluated per matching
document, so it cannot be the thing that makes a query selective. Promote it to an indexed field
once the definition stops changing.

## The hard limits and their error strings

Read from `GET /{index}/_settings?include_defaults=true&flat_settings=true` on 9.5.3:

| Setting | Default | Symptom when hit |
|---|---|---|
| `index.mapping.total_fields.limit` | 1000 | `Limit of total fields [1000] has been exceeded while adding new fields [1001]` |
| `index.mapping.depth.limit` | 20 | Deeply nested JSON rejected at index time |
| `index.mapping.nested_fields.limit` | 100 | Cannot add another `nested` field definition |
| `index.mapping.nested_objects.limit` | 10 000 | One document carries too many nested items |
| `index.max_result_window` | 10 000 | `Result window is too large, from + size must be less than or equal to: [10000]` |
| `index.max_terms_count` | 65 536 | A `terms` query with too many values |
| `index.max_docvalue_fields_search` | 100 | Too many `docvalue_fields` in one search |

Every one of these is raisable and almost none of them should be raised. They exist because the
resource they bound (cluster state size, heap per request, coordinating-node memory) fails much
less gracefully than the limit does.

## Index templates and component templates

An index template applies settings, mappings and aliases to indices whose names match a pattern, at
creation time only. Editing a template never touches existing indices.

- Composable templates (`PUT /_index_template/{name}`) with `composed_of: [...]` referencing
  component templates (`PUT /_component_template/{name}`) is the current mechanism; there is exactly
  one matching index template per index, chosen by `priority`.
- A template with a `data_stream: {}` block creates data streams instead of plain indices.
- Put the shared analysis chain and the `@timestamp`/ECS-ish core in component templates and keep
  the per-dataset mapping in the index template; that is the only way to change one field for
  twenty datasets without twenty edits.

## Changing a mapping that already exists

Mappings are append-only. You can add a field, add a multi-field, and widen a few settings such as
`ignore_above`. You cannot change a field's type, its analyzer, its `index` flag or its
`doc_values` flag — in any version. `PUT /{index}/_mapping` either rejects the change or silently
does not apply it to existing documents.

The path is always the same:

1. Create the new index with the corrected mapping under a new name (`events-000002`).
2. `POST /_reindex` from the old index; for anything large use `wait_for_completion=false`, keep the
   task id, and set `slices: auto`.
3. Compare `GET /{index}/_count` on both sides, and spot-check `GET /{index}/_mapping`.
4. Swap the alias atomically with `POST /_aliases` (`remove` + `add` in one request) so no request
   sees either both indices or neither.

Which is why every index that matters is created behind an alias on day one, before there is a
reason to. Retrofitting an alias means an application deploy, and application deploys are the part
you cannot do atomically.

<!-- sources: elastic-agent-skills, clawic-elasticsearch, elastic-docs, vespa-es-migration -->

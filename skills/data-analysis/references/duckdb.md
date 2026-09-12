# DuckDB: local file queries without changing the metric

Verified against: DuckDB 1.5.5 release and current CSV, aggregate, and workload
documentation. API semantics are [official]; examples are analytical patterns,
not database administration instructions.

## Contents

- File readers and schema contracts
- Join grain and missing measures
- Filters and time windows
- Scale, spilling, and output

## File readers and schema contracts

Use the reader for the known format rather than a macro that guesses readers
for every file type. `DESCRIBE SELECT * FROM read_csv('input.csv');` exposes the
inferred schema, not the intended identifier or missingness semantics. A small
sample cannot certify every row. Pin critical types after inspecting the source.

For a three-column input whose empty measurements mean unknown but whose
identifier strings must remain intact:

```sql
CREATE TEMP VIEW measurements AS
SELECT * FROM read_csv(
    'measurements.csv',
    header = true,
    columns = {
        'reading_id': 'VARCHAR',
        'entity_id': 'VARCHAR',
        'value': 'DECIMAL(18,4)'
    },
    nullstr = '',
    force_not_null = ['reading_id', 'entity_id']
);
```

This preserves an empty identifier as an empty string for explicit identity
validation; it does not declare that empty is a valid entity. `NA` remains text,
and leading zeros remain present. Normalize contractually missing identifiers
with an explicit transformation after counting them. `all_varchar=true` disables
type detection but does not disable null interpretation. For multiple files,
freeze the selected file list and reconcile schema; `union_by_name` may introduce
null columns and is not approval for unexpected schema drift.

Do not set `ignore_errors`, `store_rejects`, or relaxed parsing to obtain a clean
success without an exclusion ledger. `store_rejects` skips faulty rows; count
and inspect the rejects within the authorized data boundary. For coercion,
count failed casts separately from original nulls. Quoted null-token handling
is also a parser decision (`allow_quoted_nulls`), not a universal CSV rule.

## Join grain and missing measures

Probe the required unique side before joining:

```sql
SELECT entity_id, count(*) AS n
FROM dimension
WHERE entity_id IS NOT NULL
GROUP BY entity_id
HAVING count(*) > 1;
```

Decide whether repetitions are revisions, conflicting attributes, or a genuine
one-to-many relationship. Do not use arbitrary `first` to mask ambiguity. A
latest-record policy needs a complete, deterministic ordering including ties.
Ordinary equality joins do not match NULL keys; avoid null-safe equality or
shared sentinels unless matching unknown identities is explicitly meaningful.

Keep distinct facts apart until they share the required output grain. Joining
two child fact tables before summing produces the product of child rows. Use
separate grouped relations and join their one-row-per-parent summaries. Check
each amount against the original fact, not against another aggregation over the
same exploded join. `SUM(DISTINCT amount)` removes equal values, not duplicates
of the same event, and therefore corrupts legitimate equal transactions.

Carry coverage alongside each measure:

```sql
SELECT group_id,
       count(*) AS eligible_rows,
       count(value) AS observed_rows,
       count(*) - count(value) AS missing_rows,
       sum(value) AS observed_subtotal,
       avg(value) AS observed_mean
FROM eligible_measurements
GROUP BY group_id;
```

Here the declared unit must actually be one eligible row; otherwise finish the
entity-level aggregation first. `count(*)` counts rows; `count(value)` counts
non-NULL values; `avg(value)` excludes NULL. `sum` is NULL for no non-NULL inputs,
not zero. A mixed known/unknown group still produces only a subtotal. Use the
eligibility roster as the left side when entire entities have no measurement
rows, and count fact IDs rather than the outer join's synthetic row.

Distinguish no matching child event from a matched event with unknown amount.
Only the first may represent zero under a complete event-source contract.
Unconditional `COALESCE(child_sum, 0)` erases that difference. Preserve child
row and observed-amount counts before choosing the zero policy.

## Filters and time windows

Keep `WHERE` eligibility predicates separate from `HAVING` aggregate predicates.
Apply display filters and LIMIT outside global denominator/window calculations.
Use a scalar aggregate relation for a population-wide denominator; a cross join
is safe only when that relation is guaranteed to return exactly one row.

Resolve source timestamps into instants before comparing them. For a business
day, obtain the two local calendar endpoints in the named IANA timezone, convert
them to explicit UTC instants, and bind those endpoints into `ts >= start AND
 ts < end`. Do not rely on the connection's timezone when casting a date to a
timestamp. A fixed 24-hour increment does not define all local calendar days.
Document whether a source field is an instant or a naive wall-clock timestamp;
casting cannot invent missing offset/ambiguity information.

Use a total ORDER BY for published rankings, including tie-breakers. `first`,
`last`, `list`, and `string_agg` need an explicit ordering when their sequence
matters. SQL row order without ORDER BY is not a reproducibility contract.

## Scale, spilling, and output

Use `EXPLAIN` to inspect a plan without execution; `EXPLAIN ANALYZE` executes the
query and reports runtime/cardinality. Do not profile a costly or side-effecting
statement as though EXPLAIN ANALYZE were read-only planning.

DuckDB can spill joins, sorts, grouping, and window workloads to disk. Ensure a
writable temporary location with adequate free space before a large run. Multiple
blocking operators can still exhaust memory; list/string aggregation and some
complex aggregate states cannot spill. PIVOT inherits list-state limitations.
An engine memory setting is not proof of a total process-memory bound.

Project only needed columns and avoid fetching large results into Python.
After the analytical relation is correct, persist a derived typed result:

```sql
COPY (SELECT * FROM final_result ORDER BY entity_id)
TO 'derived-result.parquet' (FORMAT PARQUET);
```

Choose a fresh path or obtain explicit overwrite authorization. Order only when
the output contract needs it; sorting is itself a blocking operation. For CSV,
record the output missing token, precision, timestamp format, and identifier
read types, then validate a round trip. Bound the displayed preview separately
from the full persisted result. Do not silently install extensions or establish
remote connections for a local CSV/Parquet analysis.

<!-- sources: duckdb-official, duckdb-csv, duckdb-aggregates, duckdb-workloads -->

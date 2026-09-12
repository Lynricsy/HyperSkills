# Polars: preserve semantics across lazy execution

Verified against: Polars 1.44.2 Python API documentation and the official
streaming user guide. API claims are [official]. `nulls_equal` requires 1.24+;
inspect the installed signature before adapting older code.

## Contents

- Scans and expressions
- Identity, nulls, and joins
- Population boundaries in a lazy plan
- Opaque UDF promises
- Streaming and output memory

## Scans and expressions

Keep existing LazyFrame contracts lazy. Start file pipelines with `scan_csv` or
`scan_parquet`; avoid `read_csv(...).lazy()` when the file need not be eager.
Use `schema_overrides` for identifiers and contract-sensitive measures, and
explicit per-column `null_values` where supported. `collect_schema()` resolves
types but can perform I/O and CSV inference; it is not a full data validation or
a promise that no bytes are read. Inspect partitions beyond the inference sample.

Prefer native expressions to Python UDFs for operations the engine understands.
Give derived columns distinct aliases; a derived expression inherits its source
name, so selecting it alongside the original can raise `DuplicateError`.
Use `pl.lit("label")` for a literal in `then`/`otherwise`; bare strings name columns.
Expressions in one `with_columns` context do not form a sequential assignment
chain: introduce a second context when a new expression depends on an alias
created by the first. Do not merge these contexts as a cosmetic optimization.

A permissive cast converts invalid values into null. Count those new nulls and
retain raw values in a controlled reject artifact instead of treating the cast
as cleaning evidence. Null and floating NaN are different states in Polars;
`fill_null` and null counts do not account for NaN or infinity.

## Identity, nulls, and joins

Use `pl.len()` for rows and `pl.col("value").count()` for non-null measurements.
An ordinary sum does not establish completeness; carry non-null count and missing
count, and explicitly retain null for an all-unknown measure if the contract
requires it. A filter retains only true predicates: a comparison involving null
can drop unknown observations. Keep them explicitly if they remain eligible.

```python
result = facts.join(
    dimension,
    on="entity_id",
    how="left",
    validate="m:1",
    nulls_equal=False,
)
```

The default `m:m` validates nothing. `nulls_equal=False` leaves unknown identities
unmatched; enabling null equality requires a domain reason, not pandas parity
by accident. Check uniqueness, conflicting attributes, and unmatched counts
separately. Full joins do not coalesce key columns by default; account for both
sides before grouping. Do not depend on observed join order: explicitly sort at
the output boundary, with a stable secondary key when ranking ties matters.

## Population boundaries in a lazy plan

Classify filters as eligibility, aggregate qualification, or display selection.
A threshold on a group's sum belongs after aggregation; moving it to raw rows
changes membership. A denominator over all eligible observations must survive
later region filters and top-k. Preserve a native aggregate boundary:

```python
import polars as pl


def attach_global_fraction(base: pl.LazyFrame) -> pl.LazyFrame:
    eligible = base.filter(pl.col("eligible"))
    denominator = eligible.select(
        pl.col("value").sum().alias("observed_subtotal"),
        pl.col("value").count().alias("observed_count"),
    )
    return eligible.join(denominator, how="cross").with_columns(
        pl.when(
            (pl.col("observed_count") > 0)
            & (pl.col("observed_subtotal") != 0)
        )
        .then(pl.col("value") / pl.col("observed_subtotal"))
        .otherwise(pl.lit(None, dtype=pl.Float64))
        .alias("fraction_of_observed_subtotal")
    )
```

This is a share of observed values, not proof of a complete population total.
The caller may filter or select the returned LazyFrame; the denominator remains
its own global aggregate. Preserve the schema and lazy interface rather than
collecting inside the helper to hide optimizer interactions. Test negative or
zero totals according to the metric definition; not every signed measure is a
percentage bounded by zero and one.

## Opaque UDF promises

`LazyFrame.map_batches` cannot infer a Python function's semantics. In 1.44.2,
pushdown flags and `streamable` default to false. Setting them true asserts:

| Promise | Required equivalence |
|---|---|
| `predicate_pushdown` | Filtering before the function preserves filtering its output |
| `projection_pushdown` | Removing other columns preserves needed output and dependencies |
| `slice_pushdown` | Applying a limit/slice before the function preserves the selected output |
| `streamable` | Running on independent batches produces the same result as the whole dataset |

Global totals, normalization, ranking, and cumulative state generally violate
these promises. A function computing a sum inside its batch is not streamable
just because it returns the same number of rows. A downstream region filter
must not pass a global normalization and shrink its denominator.

Rewrite to native expressions by default. For an unavoidable UDF, keep only
proved flags enabled, keep the function pure, provide an accurate output schema,
and retain output-schema validation. Do not globally disable optimization as a
substitute for repairing one opaque boundary. The deprecated `no_optimizations`
parameter is not the recommended control (deprecated in 1.30.0).

## Streaming and output memory

`collect(engine="streaming")` executes supported work in batches, but unsupported
operations can fall back to the in-memory engine. Joins, high-cardinality group
state, sorts, and the final DataFrame can still exceed available memory. A small
preview or success on one batch cannot prove a full-data memory bound.

Inspect `lf.explain()` for logical placement and, when diagnosing streaming
memory, `lf.show_graph(plan_stage="physical", engine="streaming")` for the
physical plan. A plan is diagnostic evidence; run the actual query to observe
completion and resource use. Bound state and output before promising scalability.

Use `lf.sink_parquet("derived.parquet")` for a large typed output rather than
collecting and then writing it. Choose a new output path and preserve raw data.
A sink avoids final DataFrame materialization but does not make every upstream
operator bounded. Reopen the output and reconcile schema, nulls, and measures.

<!-- sources: polars-official, polars-streaming, polars-map-batches, polars-join -->

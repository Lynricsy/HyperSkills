# pandas: ingestion, identity, and calendar boundaries

Verified against: pandas 3.0.5 documentation. API semantics are [official];
examples are contract patterns to adapt to the actual schema, not parser defaults.

## Contents

- CSV identity survives only an explicit read contract
- Null keys and cardinality
- Counts, groups, and empty measures
- Calendar endpoints, not elapsed-day shortcuts
- Chunking is not global aggregation

## CSV identity survives only an explicit read contract

`dtype="string"` does not disable missing-token interpretation. Default NA
recognition can turn an identifier such as `NA` into missing, while numeric
inference can erase leading zeros. Declare both dtype and missing tokens:

```python
import pandas as pd

records = pd.read_csv(
    "records.csv",
    dtype={"record_id": "string", "entity_id": "string", "value": "Float64"},
    keep_default_na=False,
    na_values={"record_id": [""], "entity_id": [""], "value": ["", "N/A"]},
    on_bad_lines="error",
)
```

Here `NA` is a valid entity identifier; empty identity is missing; only the listed
measurement tokens mean unknown. Change that policy only from the source
contract. `na_filter=False` disables both `na_values` and `keep_default_na`.
Converters take precedence over dtype. Do not claim `low_memory=False` is an
out-of-core mode: without chunksize/iterator, the result is still one DataFrame.

Keep parsing strict. If invalid measurements must be quarantined, retain their
original strings and separately count `nonmissing_raw & failed_conversion`;
`errors="coerce"` alone conflates invalid data with legitimate missingness.
Check duplicate headers and inferred renamed columns before selecting fields.

## Null keys and cardinality

pandas merge matches null keys to null keys, unlike ordinary SQL and default
Polars joins. For a left enrichment where missing identity must remain unmatched,
exclude incomplete keys on the dimension side, not eligible facts:

```python
keys = ["entity_id"]
known_dimension = dimension.loc[dimension[keys].notna().all(axis=1)]
enriched = records.merge(
    known_dimension,
    on=keys,
    how="left",
    validate="many_to_one",
    indicator=True,
)
```

Inspect `_merge` for unmatched known keys separately from missing keys. The
validator checks cardinality, not whether a dimension value is factually right.
For composite keys, any missing component needs the declared policy. Do not
replace null with a shared sentinel to create matches. An intentional unknown
category can be added after identity matching without inventing a known entity.

`many_to_many` performs no uniqueness check. A left join may grow when the right
key repeats. Aggregate independent facts separately before merging; a corrected
`nunique` count leaves duplicated monetary values untouched.

## Counts, groups, and empty measures

Use `groupby(..., dropna=False)` when unknown group keys belong in the population;
the default excludes NA keys. Set `observed` deliberately when categorical
columns should enumerate only observed groups or include unused categories.
Use `size` for rows and `count` for nonmissing values. Include eligibility and
observed counts in the result rather than inferring them from a mean.

Use `sum(min_count=1)` when an all-missing measure must stay unknown; an ordinary
sum may yield zero. A group containing some known values still produces only an
observed subtotal. Preserve the missing count to prevent that subtotal being
reported as complete. Zero eligible count needs an undefined-rate policy, not a
forced zero percentage. Do not confuse index alignment with positional math:
verify entity alignment before combining Series from separate transformations.

## Calendar endpoints, not elapsed-day shortcuts

For offset-bearing ISO timestamps, parse with `pd.to_datetime(..., utc=True,
errors="raise")`. For naive local strings, parse then `tz_localize` to their
source zone; passing `utc=True` would instead assert that the wall time was UTC.
`tz_convert` changes the representation of an existing instant, not its identity.

Construct both local endpoints independently. The function below expects a
calendar date, an IANA zone, and a Series already resolved to UTC instants:

```python
from datetime import timedelta


def business_day_mask(instants, day, zone):
    start = pd.Timestamp(day).tz_localize(
        zone, ambiguous="raise", nonexistent="raise"
    ).tz_convert("UTC")
    end = pd.Timestamp(day + timedelta(days=1)).tz_localize(
        zone, ambiguous="raise", nonexistent="raise"
    ).tz_convert("UTC")
    return (instants >= start) & (instants < end)
```

Some zones have historical midnight transitions; raising exposes the missing
business rule rather than shifting records silently. For repeated wall times,
use source offsets or documented ambiguity metadata. `ambiguous="infer"` relies
on sequence structure and is not a safe guess for unsorted shards. Never strip
the timezone and then deduplicate repeated local clock labels.

## Chunking is not global aggregation

`read_csv(..., chunksize=...)` bounds input batches, not final accumulated state.
Do not append all chunks to a list and concatenate them to claim out-of-core
execution. Merge sum and observed-count states for a mean; do not average batch
means. For equal participant weighting, first finish each participant's state
across all shards, then average participant summaries.

Deduplication within each chunk misses cross-chunk retransmissions. Exact global
identity checks require memory proportional to distinct keys, or a disk-backed
index/partitioned workflow. Reordered shards and changed chunksize must preserve
identity decisions, coverage, and measures; file order is not a conflict policy.

<!-- sources: pandas-csv, pandas-merge, pandas-time, anthropic-data -->

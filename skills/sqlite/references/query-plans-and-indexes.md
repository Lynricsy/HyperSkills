# Query plans and indexes

Verified against: SQLite 3.53.0 planner documentation; bounded PRAGMA optimize
behavior since 3.46.0.

## Inspect the workload before the index

[official] Capture the exact SQL, parameter storage classes, collation, schema,
row distribution and runtime version. An integer-bound parameter and a text-bound
parameter need not reproduce the same comparisons or plan. Use the application's
binding rather than changing the workload into convenient CLI literals.

Use `EXPLAIN QUERY PLAN` to explain access, then measure the query itself with
representative data. The plan is a debugging surface whose layout and detail text
can change between releases; do not parse it as a production protocol or pin a
whole plan string as a correctness test.

| Observation | Interpretation and next check |
|---|---|
| SCAN | Visits all entries in the chosen traversal; can be an index-ordered or covering scan, not necessarily a defect |
| SEARCH with terms | Visits a subset; inspect which predicates restrict it and which remain residual filters |
| COVERING INDEX | Required values can be obtained from the index without a separate table lookup; weigh wider-index write cost |
| USE TEMP B-TREE | Sorting/grouping/distinct work not fully served by an index; inspect row count and ordering requirements |
| Multiple loops | Join nesting chosen by the planner, not necessarily the SQL FROM order; investigate a large repeated inner loop |
| Automatic index | Planner creates a statement-time index; recurring expensive use can justify a persistent one after measurement |

Do not force an index merely to remove SCAN. Tiny tables, broad predicates and
covering order scans can favor scanning. Verify selective and unselective parameter
sets; one fast lookup does not establish the workload result.

## Shape one index around the query

[community, official] Default to an index whose leftmost terms match equality
predicates, followed by useful range/order terms. Normally a gap or range term
limits how subsequent columns narrow the search; later terms may still provide
covering values or ordering. Skip-scan and OR optimizations are reasons to inspect
the actual plan instead of treating the leftmost-prefix heuristic as a theorem.

For a common query filtering by owner and ordering by creation time, consider
those terms together, not two unrelated single-column indexes. Include the
application's stable tie-breaker when order and pagination require it. Preserve
NULL ordering and collations when rewriting predicates or ordering clauses.

A covering index includes required columns as ordinary index terms; SQLite has
no PostgreSQL-style INCLUDE clause. Add payload terms only if avoided table reads
justify larger pages, storage and write amplification. Do not redundantly index
an INTEGER PRIMARY KEY rowid alias just to make its lookup "indexed".

Use a partial index only when the query's predicate implies its WHERE condition
in a form SQLite recognizes. Do not assume a parameterized status predicate will
always match a literal partial-index predicate at planning time.

An expression index (3.9.0+) matches the indexed expression syntactically apart
from minor differences such as whitespace; the planner does not prove algebraic
equivalence. `x+y` and `y+x` are not interchangeable for index matching. Indexed
expressions use deterministic functions of that table's columns, not subqueries
or another table's state. Do not falsely mark a changing function deterministic.

Do not claim JSON indexing requires a generated column; a supported expression
index can index an extraction expression directly. Choose the representation the
existing queries can consistently match, with verified function availability.

For LIKE optimization, inspect the pattern prefix, collation and the built-in
LIKE behavior; a leading wildcard and incompatible collation can defeat the
range optimization. Do not change case semantics solely to make an index appear.

## Refresh statistics deliberately

[official] On SQLite 3.46.0+, use `PRAGMA optimize` under the application's
maintenance policy; it bounds ANALYZE work itself. Do not automatically pair it
with a copied `analysis_limit` recipe or full-table ANALYZE on every request.

- For short-lived connections, the documented pattern is optimize before close.
- For long-lived connections, `PRAGMA optimize=0x10002` on initial open considers
  tables without that connection's query history; ordinary optimize then runs
  periodically and after schema changes, particularly CREATE INDEX.
- If the application intentionally ships fixed planner statistics for stable
  plans, retain that documented policy rather than silently enabling adaptation.

Treat statistics refresh as a database change, not a read-only diagnostic. On an
older runtime consult its ANALYZE/optimize documentation before applying the newer
bounded-work assumption. A new plan can regress a particular distribution;
measure again after statistics changes, not just before them.

## Close the performance claim

Report result equivalence, cardinalities, bindings, plan interpretation and
before/after latency or visited work. Where the build exposes statement scan
status, distinguish measured loop visits from planner estimates. Include added
index size and representative insert/update overhead when the index is wide or
the table is write-heavy.

Use a scratch representative dataset for DDL experiments. Retain an index only
when the workload benefit and maintenance cost support it; do not leave a pile
of candidate indexes as the outcome of investigation.

<!-- sources: openfang-sqlite, sqlite-eqp, sqlite-optimizer, sqlite-expression-indexes, sqlite-partial-indexes, sqlite-analyze -->

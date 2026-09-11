# driftwood — facts the README could have used

- GitHub repository `hallowbay/driftwood`, PyPI package `driftwood`, current
  release 1.3.0, first commit 2023-04-11.
- Two maintainers: the original author and one other person. No company behind
  it.
- What it actually does: reads the current database schema, diffs it against
  the SQL files in a migrations directory, and prints or applies the statements
  needed to reconcile them. PostgreSQL 14+ only. MySQL is not supported and
  there is no plan to support it.
- Benchmark that exists in `bench/results.md`: planning a 412-table schema takes
  1.9 s, against 26 s for the tool the author previously used (`alembic`
  autogenerate, same machine, same schema, 2026-02-14).
- `apply` runs inside one transaction on PostgreSQL. `CREATE INDEX
  CONCURRENTLY` cannot run in a transaction, so those statements are executed
  separately and are not rolled back if a later statement fails. This is
  documented nowhere in the README.
- Known unresolved design question, tracked in issue #87: whether `plan` should
  emit SQL or a machine-readable plan format. The authors have not decided.
- The test suite covers PostgreSQL 14, 15, 16 and 17 in CI.
- There is no Discord, no sponsors, no hosted demo, and no logo.

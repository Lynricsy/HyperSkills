# Spec: `tabkit dedupe`

Status: approved by @mira, 2026-09-24. Implementation owner: whoever picks up the plan.

## Why

Finance exports arrive with the same invoice repeated when an upstream job
retries. Analysts currently open the file in a spreadsheet and remove the
repeats by hand. `tabkit dedupe` removes them from the command line.

## Behaviour

`tabkit dedupe --keys COL[,COL...] [FILE]`

- Reads CSV from `FILE`, or from standard input when `FILE` is omitted or `-`.
- The first row is the header. `--keys` names one or more header columns; two
  rows are duplicates when every key column holds the same value.
- Keeps the **first** occurrence of each key and drops later ones. Row order of
  the kept rows is unchanged.
- Writes the header and the kept rows to standard output as CSV.
- Writes exactly one summary line to standard error:
  `dedupe: kept <kept> of <total> rows` (header not counted).
- Exit status 0 on success.
- Exit status 2 for a usage error (for example `--keys` missing), with the
  message printed by the argument parser.

## Examples

Input `invoices.csv`:

```csv
invoice_id,customer,amount_cents
INV-1,acme,1200
INV-2,globex,560
INV-1,acme,1200
INV-3,acme,99
```

`tabkit dedupe --keys invoice_id invoices.csv` prints the header, INV-1, INV-2
and INV-3 rows, and `dedupe: kept 3 of 4 rows` on standard error.

`tabkit dedupe --keys customer invoices.csv` keeps INV-1 and INV-2 only.

## Out of scope

- Fuzzy matching, trimming or case-folding of key values.
- Choosing which duplicate to keep (always the first).
- Formats other than CSV.

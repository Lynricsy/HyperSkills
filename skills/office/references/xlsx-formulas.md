# Formulas that survive verification

Verified against: openpyxl 3.1, LibreOffice 26.2.5.2

## Contents

- [The core problem](#the-core-problem)
- [Functions that need the _xlfn prefix](#functions-that-need-the-_xlfn-prefix)
- [Dynamic arrays do not spill](#dynamic-arrays-do-not-spill)
- [Preferred non-spilling equivalents](#preferred-non-spilling-equivalents)
- [Sheet names and references](#sheet-names-and-references)
- [Error values and what causes them](#error-values-and-what-causes-them)
- [Financial model conventions](#financial-model-conventions)
- [The recalculation gate](#the-recalculation-gate)

## The core problem

openpyxl writes the formula string you give it verbatim into the `<f>` element.
It does not translate function names, does not resolve references, and does not
evaluate anything. The stored file therefore contains no computed values at all,
and the workbook is unverified until something recalculates it.

That something is LibreOffice, which means a formula has to be written in the
form the *file format* uses, not the form Excel's formula bar shows.

## Functions that need the _xlfn prefix

Excel's UI shows `XLOOKUP(...)`. The file format stores
`_xlfn.XLOOKUP(...)`. Excel adds the prefix when it saves; openpyxl does not,
because it never parses the string. Every function introduced after Excel 2007
is affected.

Written without the prefix, both Excel and LibreOffice treat the name as an
unknown function:

| Written as | Recalculated result |
|---|---|
| `=XLOOKUP(20,A1:A3,A1:A3)` | `#NAME?` |
| `=XMATCH(20,A1:A3)` | `#NAME?` |
| `=UNIQUE(A1:A4)` | `#NAME?` |
| `=SORT(A1:A4)` | `#NAME?` |
| `=SEQUENCE(3)` | `#NAME?` |
| `=FILTER(A1:A4,A1:A4>10)` | #VALUE! |
| `=NOSUCHFN(A1)` | `#NAME?` |

With the prefix they evaluate. Note that the two worksheet-scoped functions take
a second prefix segment: `_xlfn.FILTER` and `_xlfn.SORT` still fail, while
`_xlfn._xlws.FILTER` and `_xlfn._xlws.SORT` work. `[verified]`

| Function | String to write |
|---|---|
| XLOOKUP | `=_xlfn.XLOOKUP(...)` |
| XMATCH | `=_xlfn.XMATCH(...)` |
| UNIQUE | `=_xlfn.UNIQUE(...)` |
| SEQUENCE | `=_xlfn.SEQUENCE(...)` |
| IFS | `=_xlfn.IFS(...)` |
| TEXTJOIN | `=_xlfn.TEXTJOIN(...)` |
| TEXTAFTER, TEXTBEFORE, TEXTSPLIT | `=_xlfn.TEXTAFTER(...)` etc. |
| MAXIFS, MINIFS, SWITCH, CONCAT | `=_xlfn.MAXIFS(...)` etc. |
| FILTER | `=_xlfn._xlws.FILTER(...)` |
| SORT | `=_xlfn._xlws.SORT(...)` |

Anything from Excel 2007 or earlier — `SUM`, `SUMIFS`, `INDEX`, `MATCH`,
`VLOOKUP`, `IFERROR`, `NPV`, `IRR`, `XIRR`, `PMT`, `TEXT`, `ROUND` — is written
plainly and needs no prefix.

## Dynamic arrays do not spill

Getting the prefix right is necessary and not sufficient. `FILTER`, `UNIQUE`,
`SORT` and `SEQUENCE` return arrays that Excel spills into neighbouring cells,
and spilling requires metadata (`cm`, the array `ref`) that openpyxl does not
write. The result: the anchor cell gets the first element and the rest of the
answer is lost. `=_xlfn.SEQUENCE(3)` recalculates to `1` with the two
neighbouring cells empty. `[verified]`

This is the worst failure shape in the whole format, because the recalculation
scan finds zero errors: a truncated array is not an error value. The workbook
looks verified and is wrong.

## Preferred non-spilling equivalents

Write these instead when generating a workbook programmatically. Every one of
them yields a single value per cell, so it recalculates and it verifies.

| Instead of | Write |
|---|---|
| `XLOOKUP(key, keys, values)` | `INDEX(values, MATCH(key, keys, 0))` |
| `XLOOKUP` with a not-found default | `IFERROR(INDEX(...), "n/a")` |
| `FILTER` then `SUM` | `SUMIFS(sum_range, criteria_range, criteria)` |
| `FILTER` then `COUNT` | `COUNTIFS(...)` |
| `FILTER` for a visible subset | A helper column with a flag, plus an autofilter |
| `UNIQUE` | Write the distinct values directly; you computed them already |
| `SORT` | Sort the rows before writing them |
| `SEQUENCE(n)` | Write the literal series |
| `TEXTJOIN` over a range | Join in Python and write the string |

The pattern behind the table: anything the generating script already knows
should be data, not a formula. Keep formulas for the relationships a reader will
want to change.

## Sheet names and references

- A sheet name containing a space, a hyphen or a leading digit must be quoted:
  `='Q3 Data'!A1`. Unquoted, it recalculates to #VALUE! and openpyxl accepts
  it silently. `[verified]`
- Prefer sheet names with no spaces at all, which removes the class of bug.
- Absolute references (`$B$2`) for anything pointing at an assumptions block;
  relative for the row or column a formula is meant to follow.
- Cross-workbook references (`='[other.xlsx]Sheet1'!A1`) do not recalculate
  headlessly and break as soon as the file moves. Copy the values in.
- Defined names are more readable than raw addresses in a model that people will
  edit: `wb.defined_names.add(DefinedName("growth", attr_text="Model!$B$2"))`,
  then `=B6*(1+growth)`.

## Error values and what causes them

| Value | Usual cause in a generated workbook |
|---|---|
| `#NAME?` | Missing `_xlfn.` prefix, or a genuine typo in a function name |
| #REF! | A reference to a deleted row, column or sheet |
| #VALUE! | Wrong argument type; unquoted sheet name with a space |
| #DIV/0! | Denominator cell empty or zero — wrap in `IFERROR` only when zero is legitimate |
| `#N/A` | `MATCH` or `VLOOKUP` found nothing |
| #NUM! | Iterative function did not converge, such as `IRR` with no sign change |
| #SPILL! | A dynamic array had nowhere to expand |
| #CALC! | An array function returned an empty array |

Wrapping everything in `IFERROR` hides real modelling bugs. Wrap the case you
expect (a lookup that legitimately misses) and leave the rest visible.

## Financial model conventions

Readers of a financial model expect the colour code, and it costs nothing:

| Colour | Meaning |
|---|---|
| Blue font | Hardcoded input the reader may change |
| Black font | Formula calculated on this sheet |
| Green font | Reference to another sheet in this workbook |
| Red font | Reference to another workbook — a smell to remove |
| Yellow fill | Needs review or is a placeholder |

Structure that keeps a model auditable:

- One assumptions block, at the top of the first sheet or on its own sheet.
  Every driver appears there once, with its unit and source.
- One row per line item, one column per period, no exceptions. A model where
  2027 lives in a different row than 2026 cannot be audited.
- No hardcoded numbers in calculation cells. `=B6*1.12` is unmaintainable;
  `=B6*(1+$B$2)` is the same arithmetic and answers "where does 12% come from".
- Units and periods in the row labels: "Revenue ($000s)", "Q3 2026".
- A check row where it is cheap — assets minus liabilities minus equity, or
  sources minus uses — formatted to show anything non-zero.

## The recalculation gate

```bash
uv run scripts/xlsx_recalc.py model.xlsx
```

It converts the workbook with LibreOffice, which recalculates on load, then
scans every formula cell for an error literal or a missing value and exits
non-zero if it finds one. `--json` gives machine-readable findings.

Two limits worth knowing:

- A workbook with no formulas verifies nothing; the script says so explicitly.
- A truncated dynamic array is not an error value, so the gate cannot catch it.
  That is why the equivalents table above exists.

<!-- sources: openpyxl-docs, libreoffice-docs, anthropic-xlsx -->

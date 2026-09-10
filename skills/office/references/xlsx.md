# Spreadsheets with openpyxl

Verified against: openpyxl 3.1, pandas 2.x, LibreOffice 26.2

## Contents

- [Tool per task](#tool-per-task)
- [Failure modes](#failure-modes)
- [Workbook skeleton](#workbook-skeleton)
- [Reading a workbook](#reading-a-workbook)
- [Merged cells](#merged-cells)
- [Number formats](#number-formats)
- [Column widths, freeze panes, filters](#column-widths-freeze-panes-filters)
- [Charts](#charts)
- [Macro-enabled workbooks](#macro-enabled-workbooks)
- [Large data](#large-data)
- [Delivery gate](#delivery-gate)

## Tool per task

| Task | Tool |
|---|---|
| Create or edit a workbook with formulas, styles, charts | openpyxl |
| Bulk tabular analysis, then write a plain sheet | pandas, then openpyxl for formatting |
| Read values that Excel already computed | openpyxl with `data_only=True` |
| Recalculate formulas a script just wrote | LibreOffice headless, via `scripts/xlsx_recalc.py` |
| Preserve VBA in an `.xlsm` | openpyxl with `keep_vba=True` |

## Failure modes

- **`data_only=True` plus save destroys every formula.** `data_only=True` loads
  the *cached* value and discards the formula string, so saving that workbook
  writes the values back and the model is gone. On a workbook openpyxl itself
  produced there is no cache at all, so the cells read `None` and saving turns
  the whole model into blanks. Never save a workbook that was opened with
  `data_only=True`. `[verified: openpyxl 3.1]`
- **openpyxl never evaluates anything.** A formula is stored as a string. There
  are no cached values in the output file, so a #REF! error, a misspelled function and
  a circular reference all look identical to openpyxl: fine. Recalculation is
  the only way to know.
- **openpyxl does not parse formulas either.** `"=Q3 Data!A1"` — an unquoted
  sheet name with a space — is accepted without complaint and recalculates to
  #VALUE!. `[verified]`
- **Writing to a non-anchor cell of a merged range raises.** `ws["B1"] = x`
  inside a merged `A1:C1` raises
  `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Write to
  the top-left cell. `[verified: openpyxl 3.1]`
- **`ws.max_row` counts formatting, not content.** A cell that was styled and
  then cleared still extends the used range, so iteration walks thousands of
  empty rows. Stop at the last row with data instead of trusting the bound.

## Workbook skeleton

An input-driven model separates assumptions from calculations, so a reader can
change one cell and watch everything move:

```python
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Model"

ws["A1"] = "Assumptions"
ws["A1"].font = Font(bold=True)
ws["A2"], ws["B2"] = "Growth rate", 0.12
ws["A3"], ws["B3"] = "COGS % of revenue", 0.40
for cell in ("B2", "B3"):
    ws[cell].number_format = "0.0%"

ws["A5"] = "Year"
for i, year in enumerate([2026, 2027, 2028]):
    ws.cell(row=5, column=2 + i, value=year)

ws["A6"] = "Revenue"
ws["B6"] = 1_200_000                       # the only hardcoded figure: the actual
ws["C6"] = "=B6*(1+$B$2)"                  # everything else derives from B2/B3
ws["D6"] = "=C6*(1+$B$2)"

ws["A7"] = "COGS"
ws["A8"] = "Gross profit"
ws["A9"] = "Gross margin"
for col in "BCD":
    ws[f"{col}7"] = f"={col}6*$B$3"
    ws[f"{col}8"] = f"={col}6-{col}7"
    ws[f"{col}9"] = f"={col}8/{col}6"
    ws[f"{col}9"].number_format = "0.0%"
    for row in (6, 7, 8):
        ws[f"{col}{row}"].number_format = "#,##0"

ws.freeze_panes = "B6"
for col in range(1, 5):
    ws.column_dimensions[get_column_letter(col)].width = 22 if col == 1 else 14
wb.save("model.xlsx")
```

Two habits carry most of the value: absolute references (`$B$2`) to the
assumptions block so a formula survives being copied, and one hardcoded number
per actual input, never per derived cell.

## Reading a workbook

Formulas and computed values do not coexist in one load, so reading both means
loading twice:

```python
from openpyxl import load_workbook

formulas = load_workbook("model.xlsx")                 # cell.value is "=B6*(1+$B$2)"
values = load_workbook("model.xlsx", data_only=True)   # cell.value is 1344000.0 or None
```

`values` returns `None` for every formula in a file Excel has never opened.
That is not a bug to work around by hardcoding; it is why the recalculation gate
exists.

For plain tabular data, `pandas.read_excel(path, sheet_name=None)` is faster to
write and returns a dict of frames. It gives up styles, merged cells and
formulas, so use it for analysis and openpyxl for the deliverable.

## Merged cells

```python
ws.merge_cells("A1:C1")
ws["A1"] = "Quarterly Report"    # anchor only
ws["A1"].alignment = Alignment(horizontal="center")
```

Merged ranges break sorting, filtering and structured references, and they make
`ws.cell(row, column).value` return `None` for the covered cells. Merge for
banner headings; never inside a data region.

To find them: `for rng in ws.merged_cells.ranges: print(rng)`. Unmerge with
`ws.unmerge_cells(str(rng))` before rewriting a region.

## Number formats

A number stored correctly and displayed wrongly reads as an error. Set the
format on the cell:

| Content | `number_format` |
|---|---|
| Currency | `'"$"#,##0'` or `'"$"#,##0.00'` |
| Thousands | `'#,##0'` |
| Percent (store 0.12, show 12.0%) | `'0.0%'` |
| Multiple | `'#,##0.0"x"'` |
| Date | `'yyyy-mm-dd'` |
| Negative in parentheses | `'#,##0;(#,##0)'` |

Percentages are stored as fractions. Writing `12` with a percent format shows
1200%.

## Column widths, freeze panes, filters

```python
ws.column_dimensions[get_column_letter(col)].width = max(12, len(header) + 2)
ws.freeze_panes = "B2"                      # keeps row 1 and column A visible
ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
```

There is no autofit: width is set explicitly or a column shows `#####`. Sizing
from the longest string in the column plus a couple of characters is enough.

## Charts

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.title = "Revenue by year"
chart.add_data(Reference(ws, min_col=2, max_col=4, min_row=6, max_row=6), titles_from_data=False)
chart.set_categories(Reference(ws, min_col=2, max_col=4, min_row=5, max_row=5))
ws.add_chart(chart, "F5")
```

A `Reference` points at cells, not values, so the chart tracks the model. Charts
are not rendered by openpyxl; the delivery render is the only proof one appeared.

## Macro-enabled workbooks

```python
wb = load_workbook("tool.xlsm", keep_vba=True)
...
wb.save("tool.xlsm")   # the extension must stay .xlsm
```

Without `keep_vba=True` the macros are stripped silently. Saving an `.xlsm`
workbook under an `.xlsx` name produces a file Excel refuses to open.

## Large data

Beyond roughly 100k rows, `Workbook(write_only=True)` plus `ws.append(row)`
keeps memory flat, at the cost of no random access and no post-hoc styling.
For reading, `load_workbook(path, read_only=True)` streams rows. Both modes
require closing the workbook when done.

## Delivery gate

1. `uv run scripts/xlsx_recalc.py model.xlsx` — non-zero exit means an error
   cell or an uncomputed formula. Never deliver on a non-zero exit.
2. Reopen with openpyxl (no `data_only`) to confirm the formulas are still
   formulas.
3. Render the sheet and look at it when layout matters: `#####` columns,
   misaligned headers, a chart that did not appear.

<!-- sources: openpyxl-docs, libreoffice-docs, anthropic-xlsx -->

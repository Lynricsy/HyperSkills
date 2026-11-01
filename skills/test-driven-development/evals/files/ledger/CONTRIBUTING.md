# Contributing

Run the whole suite with `python3 -m unittest -v`.
Run one file with `python3 -m unittest -v test_importer`.

`db.connect(path)` is the only way production code opens the ledger; the
import job calls `import_rows(db.connect(LEDGER_PATH), rows)`.

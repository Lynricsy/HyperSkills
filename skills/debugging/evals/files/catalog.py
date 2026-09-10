"""Loads the product catalog from the exported CSV rows.

Catalog contract: every item dict holds `name` (str), `price` (float) and
`discount_pct` (a number between 0 and 100).
"""

# One row per SKU: sku,name,unit_price,discount_percent
# The discount column is empty for SKUs that are never discounted.
RAW_ROWS = [
    "SKU-1,Widget,4.50,10",
    "SKU-2,Gasket,12.00,",
    "SKU-3,Flange,7.25,5",
]


def _parse_row(row):
    sku, name, price, discount = row.split(",")
    return sku, {
        "name": name,
        "price": float(price),
        "discount_pct": discount or "0",
    }


def load_catalog():
    return dict(_parse_row(row) for row in RAW_ROWS)

"""Line pricing.

Consumes catalog items as documented in catalog.py: `discount_pct` is a number
between 0 and 100.
"""


def discount_fraction(item):
    return item["discount_pct"] / 100


def line_total(item, qty):
    gross = item["price"] * qty
    return round(gross - gross * discount_fraction(item), 2)

"""Reporting helpers over the catalog."""


def discounted_skus(catalog):
    return sorted(sku for sku, item in catalog.items() if item["discount_pct"])

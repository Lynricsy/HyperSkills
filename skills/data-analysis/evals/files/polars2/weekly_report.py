# /// script
# requires-python = ">=3.11"
# dependencies = ["polars==2.0.0"]
# ///
"""Weekly sales report: completed revenue by region, plus the latest three orders.

orders.csv is exported newest-first by the shop backend.
"""
import polars as pl


def build(orders_path: str, customers_path: str) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    orders = pl.scan_csv(orders_path, try_parse_dates=True)
    customers = pl.scan_csv(customers_path)
    enriched = orders.join(customers, on="customer_id", how="left")

    by_region = (
        enriched.filter(pl.col("status") == "completed")
        .group_by("region")
        .agg(pl.col("amount").sum().alias("revenue"), pl.len().alias("orders"))
    )
    # the export is newest-first, so the first three rows are the latest orders
    latest = enriched.select("order_id", "created_at", "name", "amount").head(3)
    return by_region, latest


if __name__ == "__main__":
    by_region, latest = build("orders.csv", "customers.csv")
    # no_optimization: the optimizer reordered things once in 2024, keep it off
    print(by_region.collect(no_optimization=True))
    print(latest.collect(no_optimization=True))

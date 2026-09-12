# /// script
# requires-python = ">=3.11"
# dependencies = ["polars==1.44.2"]
# ///
"""Regional display of each order's share of company-wide completed revenue."""

import argparse

import polars as pl

SOURCE_SCHEMA = {
    "order_id": pl.String,
    "region": pl.String,
    "status": pl.String,
    "amount_usd": pl.Float64,
}


def add_company_share(frame: pl.DataFrame) -> pl.DataFrame:
    total = frame["amount_usd"].sum()
    return frame.with_columns(
        (pl.col("amount_usd") / total).alias("company_share")
    )


def build_report(path: str, region: str, limit: int) -> pl.LazyFrame:
    """Return a composable lazy report; region and limit are display controls."""
    return (
        pl.scan_csv(path, schema=SOURCE_SCHEMA)
        .filter(pl.col("status") == "completed")
        .map_batches(
            add_company_share,
            schema={**SOURCE_SCHEMA, "company_share": pl.Float64},
            predicate_pushdown=True,
            projection_pushdown=False,
            slice_pushdown=True,
            streamable=True,
        )
        .filter(pl.col("region") == region)
        .sort(["company_share", "order_id"], descending=[True, False], nulls_last=True)
        .head(limit)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="share_orders.csv")
    parser.add_argument("--region", default="North")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--engine", choices=["auto", "streaming"], default="auto")
    args = parser.parse_args()
    print(build_report(args.path, args.region, args.limit).collect(engine=args.engine))

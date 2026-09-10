"""Standalone weekly report puller.

Not part of the package. Ops runs it by hand:
    source /opt/acme/venv-scripts/bin/activate
    pip install requests tabulate
    python weekly_report.py --week 34
"""

import argparse
import sys

import requests
from tabulate import tabulate


def fetch(week: int) -> list[dict]:
    resp = requests.get(
        "https://reporting.internal.acme.example/weekly",
        params={"week": week},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["rows"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, required=True)
    args = parser.parse_args()
    rows = fetch(args.week)
    print(tabulate(rows, headers="keys"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

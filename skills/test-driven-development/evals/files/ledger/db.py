"""Connection factory for the ledger database."""

import sqlite3


def connect(path):
    # Explicit transaction control: callers decide when to commit.
    return sqlite3.connect(path, isolation_level=None)

"""Migration v7 for the warehouse handheld app's local database.

Goal: stock.quantity must never be negative again (a sync bug wrote -3 for a few
SKUs last month). Every build of the app links our own SQLite amalgamation, and
since app 5.2 (the oldest version still allowed to sync) that is SQLite 3.53.2
or newer, so every engine that can open this file is >= 3.53.2.

Current draft below was copied from an old migration and does the full
12-step rebuild. Review it before we ship v7.
"""

import sqlite3

SCHEMA_V6 = """
CREATE TABLE stock (
    sku        TEXT PRIMARY KEY,
    bin        TEXT NOT NULL,
    quantity   INTEGER,
    updated_at TEXT NOT NULL
);
CREATE INDEX stock_bin ON stock(bin);
CREATE TRIGGER stock_touch AFTER UPDATE OF quantity ON stock
BEGIN
    UPDATE stock SET updated_at = datetime('now') WHERE sku = NEW.sku;
END;
"""


def migrate_v7(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        PRAGMA foreign_keys = OFF;
        BEGIN;
        CREATE TABLE stock_new (
            sku        TEXT PRIMARY KEY,
            bin        TEXT NOT NULL,
            quantity   INTEGER CHECK (quantity >= 0),
            updated_at TEXT NOT NULL
        );
        INSERT INTO stock_new SELECT sku, bin, MAX(quantity, 0), updated_at FROM stock;
        DROP TABLE stock;
        ALTER TABLE stock_new RENAME TO stock;
        CREATE INDEX stock_bin ON stock(bin);
        PRAGMA user_version = 7;
        COMMIT;
        PRAGMA foreign_keys = ON;
    """)


def demo_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_V6)
    conn.executemany(
        "INSERT INTO stock VALUES (?, ?, ?, ?)",
        [
            ("SKU-1", "A1", 12, "2026-10-01"),
            ("SKU-2", "A1", -3, "2026-10-02"),
            ("SKU-3", "B4", None, "2026-10-03"),
            ("SKU-4", "C2", 0, "2026-10-04"),
        ],
    )
    conn.execute("PRAGMA user_version = 6")
    conn.commit()
    return conn


if __name__ == "__main__":
    print("sqlite", sqlite3.sqlite_version)
    c = demo_db()
    migrate_v7(c)
    print(c.execute("SELECT * FROM stock ORDER BY sku").fetchall())

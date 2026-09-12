"""Catalog migration used by a desktop app; Python 3.11+ stdlib only.

Product IDs are printed on issued receipts and must never be reused, even after
products are deleted. Shipments, price audit entries, SKU uniqueness, and the
public_catalog view are existing consumer contracts. Negative prices in an old
file require operator repair, not deletion or coercion by a migration.
"""
import sqlite3
import tempfile
from pathlib import Path


def create_legacy(path, invalid=False):
    db = sqlite3.connect(path, isolation_level=None)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
            CREATE TABLE products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                price_cents INTEGER NOT NULL
            );
            CREATE UNIQUE INDEX products_sku ON products(sku);
            CREATE TABLE shipments(
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE
            );
            CREATE TABLE price_audit(product_id INTEGER, old_price INTEGER, new_price INTEGER);
            CREATE TRIGGER product_price_changed AFTER UPDATE OF price_cents ON products
            BEGIN
                INSERT INTO price_audit VALUES(old.id, old.price_cents, new.price_cents);
            END;
            CREATE VIEW public_catalog AS SELECT id, sku, price_cents FROM products;
            INSERT INTO products(id,sku,price_cents) VALUES(1,'BOOK',1200);
            INSERT INTO products(id,sku,price_cents) VALUES(900,'RETIRED',500);
            DELETE FROM products WHERE id=900;
            INSERT INTO shipments VALUES(41,1);
            PRAGMA user_version=1;
        """)
        if invalid:
            db.execute("UPDATE products SET price_cents=-5 WHERE id=1")
    finally:
        db.close()


def migrate(db):
    """Upgrade products to strict typing with a nonnegative price constraint."""
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute("""CREATE TABLE products_new(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            price_cents INTEGER NOT NULL CHECK(price_cents>=0)
        ) STRICT""")
        db.execute("INSERT INTO products_new SELECT * FROM products")
        db.execute("DROP TABLE products")
        db.execute("ALTER TABLE products_new RENAME TO products")
        db.execute("PRAGMA user_version=2")
        db.commit()
    except BaseException:
        db.rollback()
        raise


def snapshot(db):
    return {
        "products": db.execute("SELECT * FROM products ORDER BY id").fetchall(),
        "shipments": db.execute("SELECT * FROM shipments ORDER BY id").fetchall(),
        "audit": db.execute("SELECT * FROM price_audit ORDER BY rowid").fetchall(),
        "issued_id_watermark": db.execute("SELECT seq FROM sqlite_sequence WHERE name='products'").fetchall(),
        "schema": db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall(),
        "user_version": db.execute("PRAGMA user_version").fetchone()[0],
        "foreign_keys": db.execute("PRAGMA foreign_keys").fetchone()[0],
    }


def exercise_consumers(db):
    db.execute("BEGIN")
    try:
        next_id = db.execute("INSERT INTO products(sku,price_cents) VALUES('NEW',700)").lastrowid
        db.execute("UPDATE products SET price_cents=1300 WHERE id=1")
        print("next issued id", next_id)
        print("shipments", db.execute("SELECT * FROM shipments").fetchall())
        print("catalog", db.execute("SELECT * FROM public_catalog ORDER BY id").fetchall())
        print("audit", db.execute("SELECT * FROM price_audit").fetchall())
        for label, sql in [
            ("duplicate SKU", "INSERT INTO products(sku,price_cents) VALUES('BOOK',1)"),
            ("negative price", "INSERT INTO products(sku,price_cents) VALUES('NEGATIVE',-1)"),
            ("text price", "INSERT INTO products(sku,price_cents) VALUES('TEXT','bad')"),
            ("orphan shipment", "INSERT INTO shipments VALUES(42,999999)"),
        ]:
            try:
                db.execute(sql)
                print(label, "ACCEPTED")
            except sqlite3.IntegrityError:
                print(label, "rejected")
        print("foreign key violations", db.execute("PRAGMA foreign_key_check").fetchall())
    finally:
        db.rollback()


def main():
    with tempfile.TemporaryDirectory() as directory:
        for label, invalid in [("valid", False), ("needs-repair", True)]:
            path = Path(directory) / (label + ".db")
            create_legacy(path, invalid)
            db = sqlite3.connect(path, isolation_level=None)
            try:
                db.execute("PRAGMA foreign_keys=ON")
                print(label, "linked SQLite", db.execute("SELECT sqlite_version()").fetchone()[0])
                before = snapshot(db)
                print("before", before)
                try:
                    migrate(db)
                except sqlite3.Error as error:
                    print("migration rejected", error)
                    print("state unchanged", snapshot(db) == before)
                else:
                    print("after", snapshot(db))
                    exercise_consumers(db)
            finally:
                db.close()


if __name__ == "__main__":
    main()

"""A legacy order import with referential constraints and loose column types."""
import sqlite3
import tempfile
from pathlib import Path


def import_rows(path):
    db = sqlite3.connect(path, isolation_level=None)
    try:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("BEGIN")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("INSERT INTO orders VALUES(2, 999, 'not-a-number')")
        db.commit()
        print("import FK setting", db.execute("PRAGMA foreign_keys").fetchone()[0])
    finally:
        db.close()


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "shop.db"
        setup = sqlite3.connect(path, isolation_level=None)
        setup.execute("PRAGMA foreign_keys=ON")
        setup.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY)")
        setup.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), amount INTEGER)")
        setup.execute("INSERT INTO customers VALUES(1)")
        setup.execute("INSERT INTO orders VALUES(1,1,250)")
        setup.close()
        import_rows(path)
        check = sqlite3.connect(path)
        try:
            print("linked SQLite", sqlite3.sqlite_version)
            print("integrity", check.execute("PRAGMA integrity_check").fetchall())
            print("rows", check.execute("SELECT *, typeof(amount) FROM orders").fetchall())
        finally:
            check.close()


if __name__ == "__main__":
    main()

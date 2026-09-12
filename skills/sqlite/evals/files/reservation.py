"""Two workers reserve units; run with Python 3.11+ and its linked SQLite."""
import sqlite3
import tempfile
from pathlib import Path


def reserve(db, requested, after_read):
    db.execute("BEGIN")
    available = db.execute("SELECT available FROM stock WHERE id=1").fetchone()[0]
    after_read()
    if available < requested:
        db.rollback()
        return False
    db.execute("UPDATE stock SET available=? WHERE id=1", (available - requested,))
    db.commit()
    return True


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "inventory.db"
        a = sqlite3.connect(path, isolation_level=None, timeout=0.2)
        b = sqlite3.connect(path, isolation_level=None, timeout=0.2)
        try:
            print("linked SQLite", a.execute("SELECT sqlite_version()").fetchone()[0])
            a.execute("PRAGMA journal_mode=WAL")
            a.execute("CREATE TABLE stock(id INTEGER PRIMARY KEY, available INTEGER NOT NULL)")
            a.execute("INSERT INTO stock VALUES(1, 5)")
            def competing_reservation():
                b.execute("UPDATE stock SET available=available-4 WHERE id=1")
            try:
                print("accepted", reserve(a, 3, competing_reservation))
            except sqlite3.Error as error:
                print("error", error.sqlite_errorcode, error.sqlite_errorname)
                a.rollback()
            print("remaining", b.execute("SELECT available FROM stock").fetchone()[0])
        finally:
            a.close()
            b.close()


if __name__ == "__main__":
    main()

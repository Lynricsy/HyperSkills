"""Scheduled backup of a running local SQLite database; Python stdlib only."""
import shutil
import sqlite3
import tempfile
from pathlib import Path


def export_backup(source_path, backup_path):
    shutil.copyfile(source_path, backup_path)


def main():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "orders.db"
        backup = Path(directory) / "backup.db"
        writer = sqlite3.connect(source, isolation_level=None)
        try:
            print("linked SQLite", sqlite3.sqlite_version)
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, total INTEGER)")
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            writer.execute("INSERT INTO orders VALUES(17, 950)")
            export_backup(source, backup)
            restored = sqlite3.connect(backup)
            try:
                print("integrity", restored.execute("PRAGMA integrity_check").fetchone()[0])
                print("restored orders", restored.execute("SELECT * FROM orders").fetchall())
            finally:
                restored.close()
            print("live orders", writer.execute("SELECT * FROM orders").fetchall())
        finally:
            writer.close()


if __name__ == "__main__":
    main()

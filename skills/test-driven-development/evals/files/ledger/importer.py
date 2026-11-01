"""Bulk import of ledger entries.

Contract: import_rows writes every row or none of them. If any row fails,
the ledger is left exactly as it was before the call and the error is
re-raised to the caller.
"""


def import_rows(conn, rows):
    try:
        for row in rows:
            if row["amount_cents"] is None:
                raise ValueError(f"row {row['id']} has no amount")
            conn.execute(
                "INSERT INTO entries (id, amount_cents) VALUES (?, ?)",
                (row["id"], row["amount_cents"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

"""Inventory reservation service.

Currently runs against Aurora PostgreSQL 16. We are moving the cluster to
Aurora DSQL (multi-Region, us-east-1 + us-east-2) next sprint and want to keep
this module unchanged apart from the connection string.
"""

import psycopg

from billing import charge_card  # calls the payment provider over HTTPS
from mail import send_confirmation


def reserve(conn: psycopg.Connection, sku: str, order_id: str, qty: int, card_token: str) -> None:
    with conn.transaction():
        # Row lock: a second buyer blocks here until we commit, so stock can
        # never go negative. No retry needed.
        row = conn.execute(
            "SELECT s.on_hand FROM stock s JOIN warehouses w ON w.id = s.warehouse_id "
            "WHERE s.sku = %s AND w.region = 'primary' FOR UPDATE",
            (sku,),
        ).fetchone()
        if row is None or row[0] < qty:
            raise ValueError("insufficient stock")

        charge_card(card_token, order_id)
        conn.execute(
            "UPDATE stock SET on_hand = on_hand - %s WHERE sku = %s", (qty, sku)
        )
        conn.execute(
            "INSERT INTO reservations (order_id, sku, qty) VALUES (%s, %s, %s)",
            (order_id, sku, qty),
        )
    send_confirmation(order_id)


def check_price(conn: psycopg.Connection, sku: str) -> int:
    with conn.transaction():
        # Keep the price row from changing while the cart is being totalled.
        return conn.execute(
            "SELECT price_cents FROM prices WHERE sku = %s FOR SHARE", (sku,)
        ).fetchone()[0]


def nightly_expire(conn: psycopg.Connection) -> None:
    """Release reservations older than 30 minutes (typically 20k-60k rows)."""
    with conn.transaction():
        rows = conn.execute(
            "SELECT order_id, sku, qty FROM reservations "
            "WHERE created_at < now() - interval '30 minutes' FOR UPDATE"
        ).fetchall()
        for order_id, sku, qty in rows:
            conn.execute(
                "UPDATE stock SET on_hand = on_hand + %s WHERE sku = %s", (qty, sku)
            )
            conn.execute("DELETE FROM reservations WHERE order_id = %s", (order_id,))

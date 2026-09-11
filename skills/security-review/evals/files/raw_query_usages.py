# services/api/handlers.py — excerpt collected for rule development.
#
# House rule: `db.raw_query()` bypasses the ORM's parameter binding and must never
# receive a string built from request data. `db.query()` binds parameters and is fine.
from flask import request

from . import db, settings

ALLOWED_SORTS = {"created_at", "total_cents"}


def list_orders_bad():
    sort = request.args.get("sort", "created_at")
    return db.raw_query("SELECT * FROM orders ORDER BY " + sort)


def search_orders_bad():
    term = request.get_json()["term"]
    return db.raw_query(f"SELECT * FROM orders WHERE note ILIKE '%{term}%'")


def list_orders_ok():
    sort = request.args.get("sort", "created_at")
    if sort not in ALLOWED_SORTS:
        sort = "created_at"
    return db.raw_query("SELECT * FROM orders ORDER BY " + sort)


def search_orders_ok():
    term = request.get_json()["term"]
    return db.query("SELECT * FROM orders WHERE note ILIKE %s", ("%" + term + "%",))


def nightly_rollup_ok():
    return db.raw_query(f"SELECT count(*) FROM orders WHERE tenant = '{settings.TENANT}'")

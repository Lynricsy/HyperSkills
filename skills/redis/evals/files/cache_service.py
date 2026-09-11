"""Product catalogue cache in front of Postgres. Redis 8.10, single node (not cluster).

Traffic: ~40k req/s at peak, 1.2M products, ~30k of them hot.
Incidents we keep having:
  1. Every day at 09:00 the database CPU spikes to 100% for ~90 seconds.
  2. A scraper hitting /product/<random-uuid> takes the whole site down.
  3. Sessions log users out at random even though the TTL is 24h.
  4. Twice a month Redis returns "OOM command not allowed when used memory >
     'maxmemory'" on writes and the site starts erroring.
"""

import json
import redis

r = redis.Redis(host="cache-01", port=6379, decode_responses=True)

PRODUCT_TTL = 3600  # 1 hour
SESSION_TTL = 86400  # 24 hours


def warm_cache(product_ids):
    """Called from a cron job at 08:00 every morning."""
    for pid in product_ids:
        row = db.fetch_product(pid)
        r.set(f"product:{pid}", json.dumps(row), ex=PRODUCT_TTL)


def get_product(pid):
    key = f"product:{pid}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)

    row = db.fetch_product(pid)  # ~180ms, hits Postgres
    if row is None:
        return None
    r.set(key, json.dumps(row), ex=PRODUCT_TTL)
    return row


def invalidate_category(category_id):
    """Called whenever a merchandiser edits a category."""
    for key in r.keys(f"product:*"):
        blob = r.get(key)
        if blob and json.loads(blob).get("category_id") == category_id:
            r.delete(key)


def touch_session(session_id):
    """Called on every authenticated request to keep the session alive."""
    key = f"session:{session_id}"
    raw = r.get(key)
    if raw is None:
        return None
    session = json.loads(raw)
    session["last_seen"] = now_ms()
    r.set(key, json.dumps(session))  # refresh the payload
    return session


# redis.conf on cache-01
#
#   maxmemory 24gb
#   maxmemory-policy volatile-lru
#   appendonly no
#   save 3600 1 300 100 60 10000

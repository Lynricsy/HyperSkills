"""Order-fulfilment worker + the Redis structures it uses. Redis 8.10, single node.

Known problems in production:
  - After a deploy (SIGTERM to the workers) we get support tickets about orders
    that were paid but never shipped. Nothing in the logs.
  - Two workers occasionally ship the same order twice.
  - `redis-cli --bigkeys` reports `user:index:active` as 2.3M members and
    `INFO commandstats` shows SMEMBERS averaging 41ms.
  - The dashboard endpoint that lists "recently viewed" per user got slow after
    we started storing 5000 items per user.
  - Sessions are one JSON string per user; the mobile app updates only
    `push_token` but we rewrite the whole 12 KB blob every time.
"""

import json
import redis

r = redis.Redis(host="redis-01", port=6379, decode_responses=True)


def enqueue_order(order):
    r.lpush("queue:orders", json.dumps(order))


def worker_loop():
    while True:
        raw = r.rpop("queue:orders")
        if raw is None:
            time.sleep(0.1)
            continue
        order = json.loads(raw)
        ship(order)  # takes 2-30 seconds, calls a carrier API


def mark_user_active(user_id):
    r.sadd("user:index:active", user_id)


def active_user_ids():
    return r.smembers("user:index:active")


def record_view(user_id, product_id):
    key = f"user:{user_id}:recently_viewed"
    r.lpush(key, product_id)
    r.ltrim(key, 0, 4999)


def recently_viewed(user_id):
    return r.lrange(f"user:{user_id}:recently_viewed", 0, -1)[:20]


def save_session(user_id, session):
    r.set(f"session:{user_id}", json.dumps(session), ex=86400)


def update_push_token(user_id, token):
    key = f"session:{user_id}"
    session = json.loads(r.get(key))
    session["push_token"] = token
    r.set(key, json.dumps(session), ex=86400)

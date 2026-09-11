"""We are moving from a single Redis node to a 3-primary Redis Cluster (8.10).

Everything below works today against the single node. On the cluster staging
environment we get:

  CROSSSLOT Keys in request don't hash to the same slot

...from several of these functions, and the checkout Lua script fails with

  ERR Lua script attempted to access keys of different slots

Also: the ops team says the cluster has 3 primaries and 3 replicas but reads
are still all landing on the primaries, and one shard holds 4x the keys of the
other two.
"""

import redis
from redis.cluster import RedisCluster

# Today (single node); on the cluster we plan to swap this for RedisCluster.
r = redis.Redis(host="redis-01", port=6379, decode_responses=True)


def load_user_bundle(user_id):
    return r.mget(
        f"user:{user_id}:profile",
        f"user:{user_id}:settings",
        f"user:{user_id}:entitlements",
    )


def move_to_processed(user_id, item):
    with r.pipeline(transaction=True) as pipe:
        pipe.srem(f"user:{user_id}:pending", item)
        pipe.sadd(f"user:{user_id}:processed", item)
        pipe.incr(f"user:{user_id}:processed_count")
        pipe.execute()


CHECKOUT = """
local cart = redis.call('HGETALL', KEYS[1])
if #cart == 0 then return 0 end
redis.call('DEL', KEYS[1])
redis.call('INCR', KEYS[2])
return 1
"""


def checkout(user_id):
    return r.eval(CHECKOUT, 2, f"cart:{user_id}", f"stats:orders:{user_id}")


def batch_prices(product_ids):
    pipe = r.pipeline(transaction=False)
    for pid in product_ids:
        pipe.get(f"price:{pid}")
    return pipe.execute()


def leaderboard_page(page):
    # One global sorted set with 60M members.
    return r.zrevrange("leaderboard:global", page * 50, page * 50 + 49, withscores=True)


def per_request_client():
    # Called from the request handler on every request.
    conn = redis.Redis(host="redis-01", port=6379, decode_responses=True)
    try:
        return conn.get("feature_flags")
    finally:
        conn.close()

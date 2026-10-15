"""Product search on Redis Query Engine.

Production: Redis 8.10.2 (self-managed), index created by create_index() below.

Incident (2026-10-14): semantic search fails on every call since the new
"similar products" widget shipped; keyword search keeps working.

    redis.exceptions.ResponseError: SEARCH_SYNTAX Syntax error at offset 1 near >[

The PR that added it says: "No DIALECT needed, DIALECT 2 is the default since
Redis 8" (quoting a blog post).
"""

import numpy as np
import redis

r = redis.Redis(host="search.internal", port=6379, decode_responses=False)


def create_index() -> None:
    r.execute_command(
        "FT.CREATE", "idx:products", "ON", "HASH", "PREFIX", "1", "product:",
        "SCHEMA",
        "name", "TEXT",
        "category", "TAG",
        "price", "NUMERIC", "SORTABLE",
        "embedding", "VECTOR", "HNSW", "6", "TYPE", "FLOAT32", "DIM", "384",
        "DISTANCE_METRIC", "COSINE",
    )


def keyword_search(text: str, limit: int = 10):
    return r.execute_command(
        "FT.SEARCH", "idx:products", text,
        "RETURN", "2", "name", "price", "LIMIT", "0", str(limit),
    )


def similar_products(embedding: list[float], k: int = 5):
    vec = np.asarray(embedding, dtype=np.float32).tobytes()
    return r.execute_command(
        "FT.SEARCH", "idx:products", f"*=>[KNN {k} @embedding $vec AS score]",
        "PARAMS", "2", "vec", vec,
        "SORTBY", "score",
        "RETURN", "2", "name", "score",
    )

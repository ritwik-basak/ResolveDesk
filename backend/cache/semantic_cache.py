import json
import os
import time
import uuid

import numpy as np
import redis
from dotenv import load_dotenv

from backend.models import embed_model as _embed_model

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

SIMILARITY_THRESHOLD = 0.85
TTL_SECONDS          = 2_592_000     # 30 days

EMBEDDINGS_KEY = "cache:embeddings"
ANSWERS_KEY    = "cache:answers"

# =============================================================================
# SINGLETONS — load once, reuse across all requests
# =============================================================================

_redis = redis.Redis(
    host     = os.getenv("REDIS_HOST", "localhost"),
    port     = int(os.getenv("REDIS_PORT", 6379)),
    password = os.getenv("REDIS_PASSWORD", None),
    ssl      = os.getenv("REDIS_SSL", "false").lower() == "true",
    decode_responses = True,       # always return str, not bytes
)


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _embed(text: str) -> np.ndarray:
    """Encode a single string using the shared BGE-base model (768-dim)."""
    return np.array(_embed_model.get_text_embedding(text), dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two L2-normalised vectors.
    Because both vectors are already normalised (||v|| = 1),
    dot product == cosine similarity. No division needed.
    """
    return float(np.dot(a, b))


# =============================================================================
# PUBLIC API
# =============================================================================

def get_cached_answer(query: str) -> dict | None:
    """
    Look up a cached answer for the given query.

    Returns a dict {"answer": str, "cache_hit": True} if a match is found,
    or None if no cached answer is close enough.
    """
    query_vec = _embed(query)

    all_embeddings = _redis.hgetall(EMBEDDINGS_KEY)
    if not all_embeddings:
        return None

    best_id    = None
    best_score = 0.0

    for entry_id, vec_json in all_embeddings.items():
        stored_vec = np.array(json.loads(vec_json), dtype=np.float32)
        score      = _cosine_similarity(query_vec, stored_vec)
        if score > best_score:
            best_score = score
            best_id    = entry_id

    print(f"[SemanticCache] query='{query}' | best_score={best_score:.4f} | threshold={SIMILARITY_THRESHOLD} | hit={best_score >= SIMILARITY_THRESHOLD}")

    if best_score >= SIMILARITY_THRESHOLD and best_id:
        answer_json = _redis.hget(ANSWERS_KEY, best_id)
        if answer_json:
            payload = json.loads(answer_json)
            payload["cache_hit"] = True
            return payload

    return None


def store_answer(query: str, answer: str) -> None:
    """
    Store a query-answer pair in the cache.

    Call this only for successful (non-escalated) responses.
    The entry expires after TTL_SECONDS seconds.
    """
    entry_id  = str(uuid.uuid4())
    query_vec = _embed(query)
    expire_at = int(time.time()) + TTL_SECONDS

    _redis.hset(EMBEDDINGS_KEY, entry_id, json.dumps(query_vec.tolist()))
    _redis.hset(ANSWERS_KEY,    entry_id, json.dumps({"answer": answer}))

    # Set TTL on the parent hash keys so Redis auto-cleans them.
    # EXPIREAT sets absolute expiry; using EXPIRE here for simplicity.
    _redis.expire(EMBEDDINGS_KEY, TTL_SECONDS)
    _redis.expire(ANSWERS_KEY,    TTL_SECONDS)

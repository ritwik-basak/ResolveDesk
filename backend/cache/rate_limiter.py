import os

import redis
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
WINDOW_SECONDS        = 60

# =============================================================================
# SINGLETON
# =============================================================================

_redis = redis.Redis(
    host     = os.getenv("REDIS_HOST", "localhost"),
    port     = int(os.getenv("REDIS_PORT", 6379)),
    password = os.getenv("REDIS_PASSWORD", None),
    decode_responses = True,
)


# =============================================================================
# PUBLIC API
# =============================================================================

def is_allowed(customer_email: str) -> tuple[bool, int]:
    """
    Check whether this user is within their per-minute message quota.

    Returns:
        (True,  remaining) — request allowed, remaining = how many left this minute
        (False, 0)         — rate limit exceeded
    """
    key   = f"rate_limit:{customer_email}"
    count = _redis.incr(key)

    if count == 1:
        # First message this window — start the 60-second expiry clock
        _redis.expire(key, WINDOW_SECONDS)

    if count > RATE_LIMIT_PER_MINUTE:
        return False, 0

    remaining = RATE_LIMIT_PER_MINUTE - count
    return True, remaining

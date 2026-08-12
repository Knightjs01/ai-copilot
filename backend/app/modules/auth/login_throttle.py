"""Per-account login throttling — layered on top of slowapi's per-IP rate limit in
app/core/rate_limit.py. The per-IP limit alone doesn't stop credential stuffing distributed
across many source IPs against one specific account; this catches that by keying on the
*target* email instead.

Deliberately a rolling, self-expiring window rather than a hard account lock: a permanent lock
triggered by failed attempts is itself a denial-of-service vector (anyone who knows a victim's
email can lock them out indefinitely). The threshold here is set high enough that a legitimate
user mistyping their password repeatedly won't hit it, while still meaningfully raising the cost
of a distributed brute-force/stuffing run against a single account.

is_locked returns the exact same signal a wrong password does — AuthService.login raises the
identical InvalidCredentialsError either way, so a throttled response is indistinguishable from
an ordinary failed login and reveals nothing about whether the account exists or is being
targeted.
"""

import hashlib

from redis.asyncio import Redis

from app.core.config import get_settings

_MAX_FAILURES = 15
_WINDOW_SECONDS = 15 * 60


def _get_redis() -> Redis:
    # Deliberately not a module-level singleton: redis.asyncio.Redis binds its connection pool to
    # whichever event loop is running at construction time. A per-process app has exactly one
    # long-lived loop, so this is cheap either way — but a cached client breaks across pytest's
    # per-test event loops (each test gets a fresh loop; a stale client raises "Event loop is
    # closed" on its second use). Construction itself doesn't open a socket — that happens lazily
    # on first command, so building fresh here costs nothing per call.
    return Redis.from_url(get_settings().redis_url, decode_responses=True)  # type: ignore[no-any-return]


def _key(email: str, realm: str) -> str:
    # Hashed rather than stored raw — this Redis key exists purely for throttling, no reason to
    # persist a plaintext account identifier in it. realm keeps company and candidate login
    # attempts on the same email address from sharing one counter — they're separate principals.
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"login_throttle:{realm}:{digest}"


class LoginAttemptTracker:
    """Disabled in the test environment, same convention as app.core.rate_limit's slowapi
    Limiter — tests use many deliberately-wrong-password assertions across a shared Redis
    instance, and none of that should throttle unrelated tests or itself."""

    def __init__(self, realm: str = "company") -> None:
        self._enabled = get_settings().environment != "test"
        self._realm = realm

    async def is_locked(self, email: str) -> bool:
        if not self._enabled:
            return False
        count = await _get_redis().get(_key(email, self._realm))
        return count is not None and int(count) >= _MAX_FAILURES

    async def record_failure(self, email: str) -> None:
        if not self._enabled:
            return
        redis = _get_redis()
        key = _key(email, self._realm)
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _WINDOW_SECONDS)

    async def clear(self, email: str) -> None:
        if not self._enabled:
            return
        await _get_redis().delete(_key(email, self._realm))

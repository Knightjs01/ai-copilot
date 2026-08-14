"""Redis-backed, single-use WebAuthn challenge storage. A challenge must only ever be consumed
once (replay protection) and expires quickly — get-then-delete on read enforces single-use.

Deliberately not a module-level singleton client: redis.asyncio.Redis binds its connection pool
to whichever event loop is running at construction time, which breaks under pytest-asyncio's
per-test event loops if cached at module scope — same gotcha and same fix as
app/modules/auth/login_throttle.py."""

from redis.asyncio import Redis

from app.core.config import get_settings


def _get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=False)  # type: ignore[no-any-return]


def _key(realm: str, subject: str) -> str:
    return f"webauthn_challenge:{realm}:{subject}"


class WebAuthnChallengeStore:
    """realm distinguishes company vs candidate (and registration vs authentication, if a
    caller wants that split too) so the same subject can't collide across principals. subject
    is caller-defined — typically a user/candidate id for registration, or a hash of the
    submitted email for the pre-authentication flow (mirroring login_throttle's email hashing,
    since login-flow Redis keys shouldn't carry a raw email in plaintext)."""

    def __init__(self, realm: str) -> None:
        self._realm = realm
        self._ttl = get_settings().webauthn_challenge_expire_seconds

    async def save(self, subject: str, challenge: bytes) -> None:
        await _get_redis().set(_key(self._realm, subject), challenge, ex=self._ttl)

    async def pop(self, subject: str) -> bytes | None:
        redis = _get_redis()
        key = _key(self._realm, subject)
        value: bytes | None = await redis.get(key)
        if value is not None:
            await redis.delete(key)
        return value

import uuid

from app.modules.auth.login_throttle import LoginAttemptTracker, _MAX_FAILURES


def _tracker() -> LoginAttemptTracker:
    tracker = LoginAttemptTracker(realm="test-unit")
    tracker._enabled = True  # bypass the test-environment no-op for this test only
    return tracker


async def test_locks_after_max_failures_and_clears() -> None:
    email = f"{uuid.uuid4()}@throttletest.com"
    tracker = _tracker()

    assert not await tracker.is_locked(email)

    for _ in range(_MAX_FAILURES):
        await tracker.record_failure(email)

    assert await tracker.is_locked(email)

    await tracker.clear(email)
    assert not await tracker.is_locked(email)


async def test_realms_are_independent() -> None:
    email = f"{uuid.uuid4()}@throttletest.com"
    company_tracker = LoginAttemptTracker(realm="test-company")
    candidate_tracker = LoginAttemptTracker(realm="test-candidate")
    company_tracker._enabled = True
    candidate_tracker._enabled = True

    for _ in range(_MAX_FAILURES):
        await company_tracker.record_failure(email)

    assert await company_tracker.is_locked(email)
    assert not await candidate_tracker.is_locked(email)

    await company_tracker.clear(email)


async def test_below_threshold_does_not_lock() -> None:
    email = f"{uuid.uuid4()}@throttletest.com"
    tracker = _tracker()

    for _ in range(_MAX_FAILURES - 1):
        await tracker.record_failure(email)

    assert not await tracker.is_locked(email)
    await tracker.clear(email)

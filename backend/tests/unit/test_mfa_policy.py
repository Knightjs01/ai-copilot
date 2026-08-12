from datetime import datetime, timedelta, timezone

from app.modules.auth.mfa_policy import is_mfa_grace_period_expired


def test_mfa_enabled_never_expires_regardless_of_age() -> None:
    ancient = datetime.now(timezone.utc) - timedelta(days=3650)
    assert (
        is_mfa_grace_period_expired(created_at=ancient, mfa_enabled=True, grace_period_days=7)
        is False
    )


def test_brand_new_account_within_grace_period() -> None:
    just_now = datetime.now(timezone.utc)
    assert (
        is_mfa_grace_period_expired(created_at=just_now, mfa_enabled=False, grace_period_days=7)
        is False
    )


def test_account_older_than_grace_period_without_mfa_is_expired() -> None:
    eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
    assert (
        is_mfa_grace_period_expired(
            created_at=eight_days_ago, mfa_enabled=False, grace_period_days=7
        )
        is True
    )


def test_boundary_exactly_at_grace_period_is_expired() -> None:
    # >= , not > — an account created exactly grace_period_days ago has had the full window.
    exactly_seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    assert (
        is_mfa_grace_period_expired(
            created_at=exactly_seven_days_ago, mfa_enabled=False, grace_period_days=7
        )
        is True
    )

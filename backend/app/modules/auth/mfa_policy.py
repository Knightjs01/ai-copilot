from datetime import datetime, timedelta, timezone


def is_mfa_grace_period_expired(
    *,
    created_at: datetime,
    mfa_enabled: bool,
    grace_period_days: int,
    has_webauthn_credential: bool = False,
) -> bool:
    """Shared by both principals (company User and CandidateUser) — see
    auth.dependencies.require_mfa_enrolled and candidate_auth.dependencies
    .require_candidate_mfa_enrolled. An account with MFA already on never expires; one without
    it gets grace_period_days from creation before every business-logic route starts refusing
    it, per the "mandatory MFA from day one, grace path not instant lockout" policy.

    A registered passkey satisfies this gate on its own, same as TOTP — see the module docstring
    in app/core/webauthn.py for why a WebAuthn ceremony already counts as two factors."""

    if mfa_enabled or has_webauthn_credential:
        return False
    return datetime.now(timezone.utc) - created_at >= timedelta(days=grace_period_days)

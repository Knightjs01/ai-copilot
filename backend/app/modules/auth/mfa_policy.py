from datetime import datetime, timedelta, timezone


def is_mfa_grace_period_expired(
    *, created_at: datetime, mfa_enabled: bool, grace_period_days: int
) -> bool:
    """Shared by both principals (company User and CandidateUser) — see
    auth.dependencies.require_mfa_enrolled and candidate_auth.dependencies
    .require_candidate_mfa_enrolled. An account with MFA already on never expires; one without
    it gets grace_period_days from creation before every business-logic route starts refusing
    it, per the "mandatory MFA from day one, grace path not instant lockout" policy."""

    if mfa_enabled:
        return False
    return datetime.now(timezone.utc) - created_at >= timedelta(days=grace_period_days)

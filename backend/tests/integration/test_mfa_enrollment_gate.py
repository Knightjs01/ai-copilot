import pyotp
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.integration.helpers import auth_headers, candidate_signup, signup


async def _expire_grace_period(*, table: str, email_column: str, email: str) -> None:
    # Directly back-dates created_at past the grace window — the only practical way to exercise
    # "grace period has lapsed" in a test without actually waiting mfa_grace_period_days days.
    engine = create_async_engine(get_settings().migration_database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    f"UPDATE {table} SET created_at = now() - interval '30 days' "
                    f"WHERE {email_column} = :email"
                ),
                {"email": email},
            )
    finally:
        await engine.dispose()


async def test_company_user_blocked_from_business_routes_after_grace_period_expires(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="grace-expired@acme.com")
    headers = auth_headers(owner["access_token"])

    # Within the grace period, a brand-new unenrolled account works normally.
    before = await client.get("/api/v1/projects", headers=headers)
    assert before.status_code == 200

    await _expire_grace_period(table="users", email_column="email", email="grace-expired@acme.com")

    blocked = await client.get("/api/v1/projects", headers=headers)
    assert blocked.status_code == 403

    # The enrollment path itself must never be blocked by the gate it exists to satisfy.
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["mfa_enabled"] is False

    setup_response = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]
    enable_response = await client.post(
        "/api/v1/auth/mfa/enable",
        json={"secret": secret, "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    assert enable_response.status_code == 200

    # Enrolling clears the gate even though created_at is still 30 days in the past.
    after = await client.get("/api/v1/projects", headers=headers)
    assert after.status_code == 200


async def test_candidate_blocked_from_phantom_passport_after_grace_period_expires(
    client: AsyncClient,
) -> None:
    tokens = await candidate_signup(client, email="candidate-grace-expired@example.com")
    headers = auth_headers(tokens["access_token"])

    # No Passport has been saved yet, so this 404s on its own merits — the point here is just
    # that it's a domain 404, not the MFA gate's 403, while still inside the grace period.
    before = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert before.status_code == 404

    await _expire_grace_period(
        table="candidate_users",
        email_column="email",
        email="candidate-grace-expired@example.com",
    )

    blocked = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert blocked.status_code == 403

    me = await client.get("/api/v1/candidate-auth/me", headers=headers)
    assert me.status_code == 200

"""Pins down (does not fix) a deliberate design property: access tokens are stateless JWTs with
no revocation list (task #211). Logout, session-revoke, and password-change all only revoke
*refresh* tokens (see AuthService.logout/revoke_session/reset_password and
app.modules.auth.dependencies.get_token_payload, which is a pure decode with no DB lookup) — a
still-valid access token keeps working until its natural exp (15 minutes) regardless of any of
those actions.

These are [REGRESSION] in the sense that nothing here is expected to change — but they're written
as assertions of the *current* behavior specifically so a future engineer who adds an access-token
blacklist doesn't get blindsided by a test that looks like it's asserting a bug. If revocation
semantics are intentionally tightened later, these tests should be updated deliberately, not
treated as failures to silently work around.
"""

from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, signup


async def test_access_token_survives_logout_until_natural_expiry(client: AsyncClient) -> None:
    owner = await signup(client, email="access-survives-logout@acme.com")
    headers = auth_headers(owner["access_token"])

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200


async def test_access_token_survives_specific_session_revoke(client: AsyncClient) -> None:
    owner = await signup(client, email="access-survives-revoke@acme.com")
    headers = auth_headers(owner["access_token"])

    sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    current_session_id = sessions[0]["id"]

    revoke_response = await client.delete(
        f"/api/v1/auth/sessions/{current_session_id}", headers=headers
    )
    assert revoke_response.status_code == 204

    # The refresh token behind this session is now dead...
    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401
    # ...but the access token minted from it is still honored until it naturally expires.
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200


async def test_candidate_access_token_survives_logout(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="candidate-access-survives-logout@example.com")
    headers = auth_headers(tokens["access_token"])

    logout_response = await client.post("/api/v1/candidate-auth/logout")
    assert logout_response.status_code == 204

    me_response = await client.get("/api/v1/candidate-auth/me", headers=headers)
    assert me_response.status_code == 200


async def test_access_token_survives_password_change_until_natural_expiry(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="access-survives-pwreset@acme.com")
    headers = auth_headers(owner["access_token"])

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "access-survives-pwreset@acme.com"}
    )
    assert forgot_response.status_code == 204

    # reset-password revokes all refresh tokens for the user (AuthService.reset_password) — the
    # already-issued access token is unaffected by that call, by the same stateless-JWT design.
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200

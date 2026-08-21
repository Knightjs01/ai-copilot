"""Adversarial: refresh-token reuse (theft) detection and cross-user session isolation
(task #211).

test_auth_flow.py already proves a *reused* refresh token gets 401'd. It never proves the other
half of AuthService.refresh's reuse-detection branch: that reuse revokes every session for that
user, including the legitimately-rotated-forward one the real client is still holding. [GAP] if
that fails — it would mean theft detection only inconveniences the thief, not the account.

Session-isolation tests here specifically target same-company, different-user pairs: refresh
tokens have no RLS at all (see alembic migrations for auth), so unlike most tenant-boundary tests
in this suite, isolation here is 100% application-layer with zero DB backstop either way.
"""

from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, invite_and_accept, signup


async def test_reused_refresh_token_revokes_the_legitimately_rotated_session_too(
    client: AsyncClient,
) -> None:
    await signup(client, email="reuse-kills-all@acme.com")
    old_cookie = client.cookies.get("refresh_token")

    # Legitimate rotation — the real client's session moves forward to a new refresh token.
    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie != old_cookie

    # An attacker replays the stolen, now-stale old token — reuse detected, theft response fires.
    client.cookies.set("refresh_token", old_cookie)
    reuse_response = await client.post("/api/v1/auth/refresh")
    assert reuse_response.status_code == 401

    # The legitimate, rotated-forward session must also be dead now — not just the reused one.
    client.cookies.set("refresh_token", new_cookie)
    legitimate_response = await client.post("/api/v1/auth/refresh")
    assert legitimate_response.status_code == 401


async def test_candidate_reused_refresh_token_revokes_the_legitimately_rotated_session_too(
    client: AsyncClient,
) -> None:
    await candidate_signup(client, email="candidate-reuse-kills-all@example.com")
    old_cookie = client.cookies.get("candidate_refresh_token")

    refresh_response = await client.post("/api/v1/candidate-auth/refresh")
    assert refresh_response.status_code == 200
    new_cookie = client.cookies.get("candidate_refresh_token")
    assert new_cookie != old_cookie

    client.cookies.set("candidate_refresh_token", old_cookie)
    reuse_response = await client.post("/api/v1/candidate-auth/refresh")
    assert reuse_response.status_code == 401

    client.cookies.set("candidate_refresh_token", new_cookie)
    legitimate_response = await client.post("/api/v1/candidate-auth/refresh")
    assert legitimate_response.status_code == 401


async def test_company_user_cannot_revoke_a_same_company_colleagues_session(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="colleague-isolation-owner@acme.com")
    owner_headers = auth_headers(owner["access_token"])

    member_tokens = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="colleague-isolation-member@acme.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member_tokens["access_token"])

    member_sessions = (await client.get("/api/v1/auth/sessions", headers=member_headers)).json()
    member_session_id = member_sessions[0]["id"]

    # Same company, different user — RLS would happily let either see the other's row here
    # (refresh_tokens carries no company_id/RLS at all); isolation must come from the app layer
    # filtering by the acting user's own id, not from tenant scoping.
    response = await client.delete(
        f"/api/v1/auth/sessions/{member_session_id}", headers=owner_headers
    )
    assert response.status_code == 404

    still_there = (await client.get("/api/v1/auth/sessions", headers=member_headers)).json()
    assert len(still_there) == 1


async def test_candidate_cannot_revoke_another_candidates_session(client: AsyncClient) -> None:
    tokens_a = await candidate_signup(client, email="candidate-isolation-a@example.com")
    headers_a = auth_headers(tokens_a["access_token"])
    tokens_b = await candidate_signup(client, email="candidate-isolation-b@example.com")
    headers_b = auth_headers(tokens_b["access_token"])

    sessions_b = (await client.get("/api/v1/candidate-auth/sessions", headers=headers_b)).json()
    session_b_id = sessions_b[0]["id"]

    response = await client.delete(
        f"/api/v1/candidate-auth/sessions/{session_b_id}", headers=headers_a
    )
    assert response.status_code == 404

    still_there = (await client.get("/api/v1/candidate-auth/sessions", headers=headers_b)).json()
    assert len(still_there) == 1

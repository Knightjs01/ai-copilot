from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, signup


async def test_company_login_creates_a_second_visible_session(client: AsyncClient) -> None:
    signup_data = await signup(client, email="sessions-company@acme.com")
    headers = auth_headers(signup_data["access_token"])

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "sessions-company@acme.com", "password": "correct horse battery staple"},
        headers={"User-Agent": "second-device-ua"},
    )
    assert login_response.status_code == 200

    sessions_response = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions_response.status_code == 200, sessions_response.text
    sessions = sessions_response.json()
    assert len(sessions) == 2
    assert sum(1 for s in sessions if s["is_current"]) == 1


async def test_company_can_revoke_a_specific_session(client: AsyncClient) -> None:
    signup_data = await signup(client, email="sessions-revoke@acme.com")
    headers = auth_headers(signup_data["access_token"])

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "sessions-revoke@acme.com", "password": "correct horse battery staple"},
        headers={"User-Agent": "device-two"},
    )
    assert login_response.status_code == 200

    sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    other_session = next(s for s in sessions if not s["is_current"])

    revoke_response = await client.delete(
        f"/api/v1/auth/sessions/{other_session['id']}", headers=headers
    )
    assert revoke_response.status_code == 204

    remaining = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    assert len(remaining) == 1
    assert remaining[0]["is_current"] is True


async def test_company_cannot_revoke_another_users_session(client: AsyncClient) -> None:
    owner_a = await signup(client, email="sessions-cross-a@acme.com")
    headers_a = auth_headers(owner_a["access_token"])
    owner_b = await signup(client, email="sessions-cross-b@acme-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    sessions_b = (await client.get("/api/v1/auth/sessions", headers=headers_b)).json()
    session_b_id = sessions_b[0]["id"]

    response = await client.delete(f"/api/v1/auth/sessions/{session_b_id}", headers=headers_a)
    assert response.status_code == 404

    # Company B's session is untouched.
    still_there = (await client.get("/api/v1/auth/sessions", headers=headers_b)).json()
    assert len(still_there) == 1


async def test_company_revoke_others_keeps_current_session_alive(client: AsyncClient) -> None:
    signup_data = await signup(client, email="sessions-revoke-others@acme.com")
    headers = auth_headers(signup_data["access_token"])

    for _ in range(2):
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "sessions-revoke-others@acme.com",
                "password": "correct horse battery staple",
            },
        )
        assert login_response.status_code == 200

    before = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    assert len(before) == 3

    revoke_response = await client.post("/api/v1/auth/sessions/revoke-others", headers=headers)
    assert revoke_response.status_code == 204

    after = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    assert len(after) == 1
    assert after[0]["is_current"] is True


async def test_candidate_sessions_list_and_revoke(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="sessions-candidate@example.com")
    headers = auth_headers(tokens["access_token"])

    login_response = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "sessions-candidate@example.com",
            "password": "correct horse battery staple",
        },
        headers={"User-Agent": "candidate-second-device"},
    )
    assert login_response.status_code == 200

    sessions_response = await client.get("/api/v1/candidate-auth/sessions", headers=headers)
    assert sessions_response.status_code == 200, sessions_response.text
    sessions = sessions_response.json()
    assert len(sessions) == 2

    other_session = next(s for s in sessions if not s["is_current"])
    revoke_response = await client.delete(
        f"/api/v1/candidate-auth/sessions/{other_session['id']}", headers=headers
    )
    assert revoke_response.status_code == 204

    remaining = (await client.get("/api/v1/candidate-auth/sessions", headers=headers)).json()
    assert len(remaining) == 1

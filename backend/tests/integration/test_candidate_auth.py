from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, create_project, signup


async def test_candidate_signup_and_me(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="jamie@example.com", full_name="Jamie Candidate")
    assert tokens["access_token"]

    me_response = await client.get(
        "/api/v1/candidate-auth/me", headers=auth_headers(tokens["access_token"])
    )
    assert me_response.status_code == 200, me_response.text
    body = me_response.json()
    assert body["email"] == "jamie@example.com"
    assert body["full_name"] == "Jamie Candidate"
    assert body["is_email_verified"] is False


async def test_candidate_signup_duplicate_email_rejected(client: AsyncClient) -> None:
    await candidate_signup(client, email="dup@example.com")
    response = await client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "dup@example.com",
            "password": "correct horse battery staple",
            "full_name": "Someone Else",
        },
    )
    assert response.status_code == 409


async def test_candidate_login_wrong_password_rejected(client: AsyncClient) -> None:
    await candidate_signup(client, email="login@example.com")
    response = await client.post(
        "/api/v1/candidate-auth/login",
        json={"email": "login@example.com", "password": "wrong password entirely"},
    )
    assert response.status_code == 401


async def test_candidate_login_succeeds_with_correct_password(client: AsyncClient) -> None:
    await candidate_signup(client, email="login2@example.com")
    response = await client.post(
        "/api/v1/candidate-auth/login",
        json={"email": "login2@example.com", "password": "correct horse battery staple"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


async def test_candidate_refresh_rotates_cookie(client: AsyncClient) -> None:
    signup_response = await client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "refresh@example.com",
            "password": "correct horse battery staple",
            "full_name": "Refresh Candidate",
        },
    )
    assert signup_response.status_code == 201

    refresh_response = await client.post("/api/v1/candidate-auth/refresh")
    assert refresh_response.status_code == 200, refresh_response.text
    assert refresh_response.json()["access_token"]


async def test_candidate_logout_clears_session(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": "logout@example.com",
            "password": "correct horse battery staple",
            "full_name": "Logout Candidate",
        },
    )
    logout_response = await client.post("/api/v1/candidate-auth/logout")
    assert logout_response.status_code == 204

    # The refresh cookie was cleared, so refreshing again with no cookie must fail.
    refresh_response = await client.post("/api/v1/candidate-auth/refresh")
    assert refresh_response.status_code == 401


async def test_company_token_cannot_access_candidate_routes(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@company-vs-candidate.com")
    response = await client.get(
        "/api/v1/candidate-auth/me", headers=auth_headers(owner["access_token"])
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_access_company_routes(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="crossover@example.com")
    response = await client.get("/api/v1/projects", headers=auth_headers(tokens["access_token"]))
    assert response.status_code == 401


async def test_candidate_token_cannot_access_company_routes_that_use_get_tenant_db(
    client: AsyncClient,
) -> None:
    # Specifically exercises the get_tenant_db hardening — a candidate token has no company_id
    # in its payload at all, which must be rejected cleanly (401) rather than crashing (500).
    owner = await signup(client, email="owner@tenant-db-guard.com")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    tokens = await candidate_signup(client, email="tenant-guard@example.com")
    response = await client.get(
        f"/api/v1/projects/{project['id']}", headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 401

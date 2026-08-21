from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    extract_token_from_email,
    platform_admin_headers,
    signup,
)


async def test_signup_returns_access_token_and_sets_refresh_cookie(client: AsyncClient) -> None:
    data = await signup(client, email="owner@acme.com")
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert "refresh_token" in client.cookies


async def test_signup_duplicate_email_is_rejected(client: AsyncClient) -> None:
    # No public self-service company signup exists anymore -- the equivalent real gate is
    # company_access's request intake. See test_company_access.py for dedicated coverage of the
    # duplicate-domain vs duplicate-email-specifically distinction; this is a smoke test that the
    # same email can't get a second workspace either way.
    await signup(client, email="dupe@acme.com")
    response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "company_name": "Other Co",
            "work_email": "dupe@acme.com",
            "password": "correct horse battery staple",
            "full_name": "Someone Else",
        },
    )
    assert response.status_code == 409


async def test_login_with_wrong_password_is_rejected(client: AsyncClient) -> None:
    await signup(client, email="login-test@acme.com")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-test@acme.com", "password": "wrong password entirely"},
    )
    assert response.status_code == 401


async def test_me_reflects_signed_up_owner(client: AsyncClient) -> None:
    data = await signup(client, email="me-test@acme.com", company_name="Me Test Co")
    response = await client.get("/api/v1/auth/me", headers=auth_headers(data["access_token"]))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me-test@acme.com"
    assert body["roles"] == ["Owner"]
    assert "users.invite" in body["permissions"]


async def test_verify_email_flow(client: AsyncClient, sent_emails: CapturingEmailSender) -> None:
    # signup()'s approval step goes through the service layer directly for speed, with no
    # email_sender wired through -- it never populates sent_emails. This test specifically cares
    # about the verification email, so it drives the real admin-authenticated HTTP approve route
    # instead, where get_email_sender's real dependency injection (overridden to sent_emails for
    # the whole test client) actually fires.
    password = "correct horse battery staple"
    submit_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Verify Test",
            "company_name": "Verify Test Co",
            "work_email": "verify-test@acme.com",
            "password": password,
        },
    )
    assert submit_response.status_code == 201, submit_response.text
    request_id = submit_response.json()["id"]

    admin_headers = await platform_admin_headers(client)
    approve_response = await client.post(
        f"/api/v1/company-access/requests/{request_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200, approve_response.text

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "verify-test@acme.com", "password": password}
    )
    assert login_response.status_code == 200, login_response.text
    data = login_response.json()

    token = extract_token_from_email(sent_emails)
    response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 204

    me = await client.get("/api/v1/auth/me", headers=auth_headers(data["access_token"]))
    assert me.json()["is_email_verified"] is True


async def test_refresh_rotates_token_and_old_one_becomes_invalid(client: AsyncClient) -> None:
    await signup(client, email="refresh-test@acme.com")
    old_cookie = client.cookies.get("refresh_token")

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie != old_cookie

    client.cookies.set("refresh_token", old_cookie)
    reuse_response = await client.post("/api/v1/auth/refresh")
    assert reuse_response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    await signup(client, email="logout-test@acme.com")

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


async def test_forgot_and_reset_password_flow(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    await signup(client, email="reset-test@acme.com")

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "reset-test@acme.com"}
    )
    assert forgot_response.status_code == 204
    token = extract_token_from_email(sent_emails)

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "a brand new password"},
    )
    assert reset_response.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-test@acme.com", "password": "correct horse battery staple"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-test@acme.com", "password": "a brand new password"},
    )
    assert new_login.status_code == 200


async def test_forgot_password_does_not_reveal_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody@nowhere.com"}
    )
    assert response.status_code == 204

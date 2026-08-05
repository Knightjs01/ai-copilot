import pyotp
from httpx import AsyncClient

from tests.integration.helpers import auth_headers, signup


async def test_mfa_setup_enable_and_login_challenge(client: AsyncClient) -> None:
    data = await signup(client, email="mfa-test@acme.com")
    headers = auth_headers(data["access_token"])

    setup_response = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]

    code = pyotp.TOTP(secret).now()
    enable_response = await client.post(
        "/api/v1/auth/mfa/enable", json={"secret": secret, "code": code}, headers=headers
    )
    assert enable_response.status_code == 204

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-test@acme.com", "password": "correct horse battery staple"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["mfa_required"] is True
    challenge_token = body["challenge_token"]

    wrong_code_response = await client.post(
        "/api/v1/auth/mfa/verify", json={"challenge_token": challenge_token, "code": "000000"}
    )
    assert wrong_code_response.status_code == 401

    verify_response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": challenge_token, "code": pyotp.TOTP(secret).now()},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["access_token"]


async def test_mfa_disable_requires_correct_password(client: AsyncClient) -> None:
    data = await signup(client, email="mfa-disable@acme.com")
    headers = auth_headers(data["access_token"])

    setup_response = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    secret = setup_response.json()["secret"]
    await client.post(
        "/api/v1/auth/mfa/enable",
        json={"secret": secret, "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )

    wrong_password = await client.post(
        "/api/v1/auth/mfa/disable", json={"password": "not the right password"}, headers=headers
    )
    assert wrong_password.status_code == 401

    correct_password = await client.post(
        "/api/v1/auth/mfa/disable",
        json={"password": "correct horse battery staple"},
        headers=headers,
    )
    assert correct_password.status_code == 204

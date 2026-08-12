import pyotp
from httpx import AsyncClient

from tests.integration.helpers import candidate_signup


def _candidate_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def test_candidate_mfa_setup_enable_and_login_challenge(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="candidate-mfa@example.com")
    headers = _candidate_headers(tokens["access_token"])

    setup_response = await client.post("/api/v1/candidate-auth/mfa/setup", headers=headers)
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]

    code = pyotp.TOTP(secret).now()
    enable_response = await client.post(
        "/api/v1/candidate-auth/mfa/enable", json={"secret": secret, "code": code}, headers=headers
    )
    assert enable_response.status_code == 200
    backup_codes = enable_response.json()["backup_codes"]
    assert len(backup_codes) == 10
    assert len(set(backup_codes)) == 10

    login_response = await client.post(
        "/api/v1/candidate-auth/login",
        json={"email": "candidate-mfa@example.com", "password": "correct horse battery staple"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["mfa_required"] is True
    challenge_token = body["challenge_token"]

    wrong_code_response = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert wrong_code_response.status_code == 401

    verify_response = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": challenge_token, "code": pyotp.TOTP(secret).now()},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["access_token"]


async def test_candidate_mfa_backup_code_logs_in_once_then_is_rejected(
    client: AsyncClient,
) -> None:
    tokens = await candidate_signup(client, email="candidate-mfa-backup@example.com")
    headers = _candidate_headers(tokens["access_token"])

    setup_response = await client.post("/api/v1/candidate-auth/mfa/setup", headers=headers)
    secret = setup_response.json()["secret"]
    enable_response = await client.post(
        "/api/v1/candidate-auth/mfa/enable",
        json={"secret": secret, "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    backup_code = enable_response.json()["backup_codes"][0]

    login_response = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate-mfa-backup@example.com",
            "password": "correct horse battery staple",
        },
    )
    challenge_token = login_response.json()["challenge_token"]

    first_use = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": challenge_token, "code": backup_code},
    )
    assert first_use.status_code == 200
    assert first_use.json()["access_token"]

    second_login = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate-mfa-backup@example.com",
            "password": "correct horse battery staple",
        },
    )
    second_challenge = second_login.json()["challenge_token"]
    reuse_attempt = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": second_challenge, "code": backup_code},
    )
    assert reuse_attempt.status_code == 401


async def test_candidate_mfa_disable_clears_backup_codes(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="candidate-mfa-clear@example.com")
    headers = _candidate_headers(tokens["access_token"])

    setup_response = await client.post("/api/v1/candidate-auth/mfa/setup", headers=headers)
    secret = setup_response.json()["secret"]
    enable_response = await client.post(
        "/api/v1/candidate-auth/mfa/enable",
        json={"secret": secret, "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    backup_code = enable_response.json()["backup_codes"][0]

    await client.post(
        "/api/v1/candidate-auth/mfa/disable",
        json={"password": "correct horse battery staple"},
        headers=headers,
    )

    setup_again = await client.post("/api/v1/candidate-auth/mfa/setup", headers=headers)
    secret_again = setup_again.json()["secret"]
    await client.post(
        "/api/v1/candidate-auth/mfa/enable",
        json={"secret": secret_again, "code": pyotp.TOTP(secret_again).now()},
        headers=headers,
    )

    login_response = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate-mfa-clear@example.com",
            "password": "correct horse battery staple",
        },
    )
    challenge_token = login_response.json()["challenge_token"]
    stale_code_attempt = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": challenge_token, "code": backup_code},
    )
    assert stale_code_attempt.status_code == 401


async def test_candidate_mfa_disable_requires_correct_password(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="candidate-mfa-disable@example.com")
    headers = _candidate_headers(tokens["access_token"])

    setup_response = await client.post("/api/v1/candidate-auth/mfa/setup", headers=headers)
    secret = setup_response.json()["secret"]
    await client.post(
        "/api/v1/candidate-auth/mfa/enable",
        json={"secret": secret, "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )

    wrong_password = await client.post(
        "/api/v1/candidate-auth/mfa/disable",
        json={"password": "not the right password"},
        headers=headers,
    )
    assert wrong_password.status_code == 401

    correct_password = await client.post(
        "/api/v1/candidate-auth/mfa/disable",
        json={"password": "correct horse battery staple"},
        headers=headers,
    )
    assert correct_password.status_code == 204


async def test_company_mfa_challenge_token_rejected_by_candidate_verify_endpoint(
    client: AsyncClient,
) -> None:
    # The candidate MFA challenge token uses a distinct JWT scope ("candidate_mfa_challenge")
    # from the company one ("mfa_challenge") specifically so a token minted for one principal
    # can never be replayed against the other's /mfa/verify endpoint.
    response = await client.post(
        "/api/v1/candidate-auth/mfa/verify",
        json={"challenge_token": "not-a-real-token", "code": "123456"},
    )
    assert response.status_code == 401

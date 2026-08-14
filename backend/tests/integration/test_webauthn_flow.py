import json

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from webauthn.helpers import base64url_to_bytes

from app.core.config import get_settings
from tests.integration.helpers import auth_headers, candidate_signup, signup
from tests.integration.webauthn_helpers import VirtualAuthenticator


async def _expire_grace_period(*, table: str, email_column: str, email: str) -> None:
    # Same back-dating technique as test_mfa_enrollment_gate.py — duplicated rather than
    # imported from that module to keep this file's fixtures self-contained.
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


async def _register_passkey(
    client: AsyncClient, *, base_path: str, headers: dict, device_name: str = "Test Key"
) -> VirtualAuthenticator:
    options_response = await client.post(f"{base_path}/webauthn/register/options", headers=headers)
    assert options_response.status_code == 200, options_response.text
    options = options_response.json()["options"]
    challenge = base64url_to_bytes(json.loads(options)["challenge"])

    authenticator = VirtualAuthenticator()
    credential = authenticator.register(challenge)

    verify_response = await client.post(
        f"{base_path}/webauthn/register/verify",
        json={"credential": credential, "device_name": device_name},
        headers=headers,
    )
    assert verify_response.status_code == 200, verify_response.text
    return authenticator


async def test_company_webauthn_registration_list_and_delete(client: AsyncClient) -> None:
    owner = await signup(client, email="webauthn-reg@acme.com")
    headers = auth_headers(owner["access_token"])

    authenticator = await _register_passkey(client, base_path="/api/v1/auth", headers=headers)

    list_response = await client.get("/api/v1/auth/webauthn/credentials", headers=headers)
    assert list_response.status_code == 200
    credentials = list_response.json()
    assert len(credentials) == 1
    assert credentials[0]["device_name"] == "Test Key"

    delete_response = await client.delete(
        f"/api/v1/auth/webauthn/credentials/{credentials[0]['id']}", headers=headers
    )
    assert delete_response.status_code == 204

    list_after = await client.get("/api/v1/auth/webauthn/credentials", headers=headers)
    assert list_after.json() == []
    assert authenticator.credential_id  # sanity: authenticator was actually used


async def test_company_webauthn_login_flow(client: AsyncClient) -> None:
    email = "webauthn-login@acme.com"
    owner = await signup(client, email=email)
    headers = auth_headers(owner["access_token"])
    authenticator = await _register_passkey(client, base_path="/api/v1/auth", headers=headers)

    options_response = await client.post(
        "/api/v1/auth/webauthn/authenticate/options", json={"email": email}
    )
    assert options_response.status_code == 200
    options = json.loads(options_response.json()["options"])
    challenge = base64url_to_bytes(options["challenge"])

    credential = authenticator.authenticate(challenge)
    verify_response = await client.post(
        "/api/v1/auth/webauthn/authenticate/verify",
        json={"email": email, "credential": credential},
    )
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json()["access_token"]


async def test_company_webauthn_authenticate_options_does_not_reveal_account_existence(
    client: AsyncClient,
) -> None:
    real_response = await client.post(
        "/api/v1/auth/webauthn/authenticate/options",
        json={"email": "webauthn-login@acme.com"},
    )
    fake_response = await client.post(
        "/api/v1/auth/webauthn/authenticate/options",
        json={"email": "definitely-not-a-real-account@acme.com"},
    )
    assert real_response.status_code == fake_response.status_code == 200
    assert "options" in real_response.json()
    assert "options" in fake_response.json()


async def test_company_webauthn_registration_satisfies_mandatory_mfa_gate(
    client: AsyncClient,
) -> None:
    email = "webauthn-mfa-gate@acme.com"
    owner = await signup(client, email=email)
    headers = auth_headers(owner["access_token"])

    await _expire_grace_period(table="users", email_column="email", email=email)

    blocked = await client.get("/api/v1/projects", headers=headers)
    assert blocked.status_code == 403

    await _register_passkey(client, base_path="/api/v1/auth", headers=headers)

    after = await client.get("/api/v1/projects", headers=headers)
    assert after.status_code == 200


async def test_candidate_webauthn_registration_list_and_delete(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="webauthn-candidate-reg@example.com")
    headers = auth_headers(tokens["access_token"])

    await _register_passkey(client, base_path="/api/v1/candidate-auth", headers=headers)

    list_response = await client.get("/api/v1/candidate-auth/webauthn/credentials", headers=headers)
    assert list_response.status_code == 200
    credentials = list_response.json()
    assert len(credentials) == 1

    delete_response = await client.delete(
        f"/api/v1/candidate-auth/webauthn/credentials/{credentials[0]['id']}", headers=headers
    )
    assert delete_response.status_code == 204


async def test_candidate_webauthn_login_flow(client: AsyncClient) -> None:
    email = "webauthn-candidate-login@example.com"
    tokens = await candidate_signup(client, email=email)
    headers = auth_headers(tokens["access_token"])
    authenticator = await _register_passkey(
        client, base_path="/api/v1/candidate-auth", headers=headers
    )

    options_response = await client.post(
        "/api/v1/candidate-auth/webauthn/authenticate/options", json={"email": email}
    )
    assert options_response.status_code == 200
    options = json.loads(options_response.json()["options"])
    challenge = base64url_to_bytes(options["challenge"])

    credential = authenticator.authenticate(challenge)
    verify_response = await client.post(
        "/api/v1/candidate-auth/webauthn/authenticate/verify",
        json={"email": email, "credential": credential},
    )
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json()["access_token"]


async def test_candidate_webauthn_registration_satisfies_mandatory_mfa_gate(
    client: AsyncClient,
) -> None:
    email = "webauthn-candidate-mfa-gate@example.com"
    tokens = await candidate_signup(client, email=email)
    headers = auth_headers(tokens["access_token"])

    await _expire_grace_period(table="candidate_users", email_column="email", email=email)

    blocked = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert blocked.status_code == 403

    await _register_passkey(client, base_path="/api/v1/candidate-auth", headers=headers)

    after = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert after.status_code == 404  # gate cleared; 404 is the domain "no Passport yet" response

import json

import pyotp
from httpx import AsyncClient
from webauthn.helpers import base64url_to_bytes

from tests.integration.helpers import auth_headers, signup, step_up_headers
from tests.integration.webauthn_helpers import VirtualAuthenticator


async def test_step_up_rejects_wrong_password(client: AsyncClient) -> None:
    owner = await signup(client, email="stepup-wrongpass@acme.com")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/auth/step-up", json={"password": "not the right password"}, headers=headers
    )
    assert response.status_code == 401


async def test_step_up_refuses_rather_than_downgrade_for_passkey_only_account(
    client: AsyncClient,
) -> None:
    # A user whose only enrolled factor is a passkey (mfa_enabled stays False -- only TOTP
    # enrollment sets it) must not have step-up silently accept password alone, since that would
    # falsely represent a single-factor check as MFA-backed. No real WebAuthn step-up ceremony
    # exists yet, so this must refuse (501), not succeed.
    owner = await signup(client, email="stepup-passkey-only@acme.com")
    headers = auth_headers(owner["access_token"])

    options_response = await client.post("/api/v1/auth/webauthn/register/options", headers=headers)
    assert options_response.status_code == 200, options_response.text
    options = options_response.json()["options"]
    challenge = base64url_to_bytes(json.loads(options)["challenge"])

    authenticator = VirtualAuthenticator()
    credential = authenticator.register(challenge)
    verify_response = await client.post(
        "/api/v1/auth/webauthn/register/verify",
        json={"credential": credential, "device_name": "Test Key"},
        headers=headers,
    )
    assert verify_response.status_code == 200, verify_response.text

    step_up_response = await client.post(
        "/api/v1/auth/step-up",
        json={"password": "correct horse battery staple"},
        headers=headers,
    )
    assert step_up_response.status_code == 501


async def test_step_up_token_grants_access_to_gated_action(client: AsyncClient) -> None:
    owner = await signup(client, email="stepup-invite@acme.com")
    headers = auth_headers(owner["access_token"])

    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": "invitee@acme.com", "full_name": "Invitee", "role": "Recruiter"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert invite_response.status_code == 201, invite_response.text


async def test_gated_action_rejected_without_step_up_token(client: AsyncClient) -> None:
    owner = await signup(client, email="stepup-missing@acme.com")
    headers = auth_headers(owner["access_token"])

    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": "invitee2@acme.com", "full_name": "Invitee", "role": "Recruiter"},
        headers=headers,
    )
    assert invite_response.status_code == 403


async def test_gated_action_rejected_with_malformed_step_up_token(client: AsyncClient) -> None:
    owner = await signup(client, email="stepup-malformed@acme.com")
    headers = auth_headers(owner["access_token"])

    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": "invitee3@acme.com", "full_name": "Invitee", "role": "Recruiter"},
        headers={**headers, "X-Step-Up-Token": "not-a-real-token"},
    )
    assert invite_response.status_code == 403


async def test_step_up_token_scoped_to_the_user_it_was_issued_for(client: AsyncClient) -> None:
    owner_a = await signup(client, email="stepup-cross-a@acme.com")
    headers_a = auth_headers(owner_a["access_token"])
    owner_b = await signup(client, email="stepup-cross-b@acme-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    # A valid step-up token, but minted for owner A's identity.
    token_for_a = (await step_up_headers(client, headers=headers_a))["X-Step-Up-Token"]

    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": "invitee4@acme.com", "full_name": "Invitee", "role": "Recruiter"},
        headers={**headers_b, "X-Step-Up-Token": token_for_a},
    )
    assert invite_response.status_code == 403


async def test_step_up_requires_mfa_code_when_account_has_mfa_enabled(client: AsyncClient) -> None:
    owner = await signup(client, email="stepup-mfa@acme.com")
    headers = auth_headers(owner["access_token"])

    setup_response = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    secret = setup_response.json()["secret"]
    await client.post(
        "/api/v1/auth/mfa/enable",
        json={
            "password": "correct horse battery staple",
            "secret": secret,
            "code": pyotp.TOTP(secret).now(),
        },
        headers=headers,
    )

    missing_code = await client.post(
        "/api/v1/auth/step-up",
        json={"password": "correct horse battery staple"},
        headers=headers,
    )
    assert missing_code.status_code == 401

    with_code = await client.post(
        "/api/v1/auth/step-up",
        json={
            "password": "correct horse battery staple",
            "mfa_code": pyotp.TOTP(secret).now(),
        },
        headers=headers,
    )
    assert with_code.status_code == 200
    assert with_code.json()["step_up_token"]

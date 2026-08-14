"""Adversarial: forged/tampered JWT claims presented to real endpoints (task #211).

Every test here mints a token whose bytes are individually attacker-plausible (a real signing
key, a real signature, or a real prior token used out of context) but whose *meaning* is wrong —
and asserts the app rejects it. All [REGRESSION]: these prove properties the app already claims,
not properties this file introduces.
"""

import base64
import json
import uuid

import jwt
from httpx import AsyncClient

from app.modules.auth import security
from tests.integration.helpers import (
    auth_headers,
    candidate_signup,
    forge_access_token,
    forge_candidate_access_token,
    signup,
)


async def test_valid_signature_wrong_company_id_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="forge-wrong-company@acme.com")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(owner["access_token"]))
    user_id = uuid.UUID(me.json()["id"])

    # Real user, real signature, but a company_id the user doesn't actually belong to.
    forged = forge_access_token(user_id=user_id, company_id=uuid.uuid4())
    response = await client.get("/api/v1/auth/me", headers=auth_headers(forged))
    assert response.status_code == 401


async def test_valid_signature_nonexistent_user_id_is_rejected_not_500(client: AsyncClient) -> None:
    forged = forge_access_token(user_id=uuid.uuid4(), company_id=uuid.uuid4())
    response = await client.get("/api/v1/auth/me", headers=auth_headers(forged))
    assert response.status_code == 401


async def test_valid_signature_nonexistent_candidate_id_is_rejected(client: AsyncClient) -> None:
    forged = forge_candidate_access_token(candidate_id=uuid.uuid4())
    response = await client.get("/api/v1/candidate-auth/me", headers=auth_headers(forged))
    assert response.status_code == 401


async def test_token_signed_with_a_different_key_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="forge-wrong-key@acme.com")
    payload = security.decode_access_token(owner["access_token"])

    resigned = jwt.encode(payload, "an-attacker-controlled-key", algorithm=security.JWT_ALGORITHM)
    response = await client.get("/api/v1/auth/me", headers=auth_headers(resigned))
    assert response.status_code == 401


async def test_unsigned_alg_none_token_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="forge-alg-none@acme.com")
    payload = security.decode_access_token(owner["access_token"])

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    # PyJWT refuses to encode alg=none by default, so this is built by hand — the exact shape an
    # attacker who controls only the wire bytes (not the library) would send.
    header = _b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    body = _b64url(json.dumps(payload, default=str).encode())
    unsigned_token = f"{header}.{body}."

    response = await client.get("/api/v1/auth/me", headers=auth_headers(unsigned_token))
    assert response.status_code == 401


async def test_mfa_challenge_token_is_not_accepted_as_a_bearer_access_token(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="forge-mfa-challenge@acme.com")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(owner["access_token"]))
    user_id = uuid.UUID(me.json()["id"])

    challenge_token = security.create_mfa_challenge_token(user_id=user_id)
    response = await client.get("/api/v1/auth/me", headers=auth_headers(challenge_token))
    assert response.status_code == 401


async def test_step_up_token_is_not_accepted_as_a_bearer_access_token(client: AsyncClient) -> None:
    owner = await signup(client, email="forge-step-up@acme.com")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(owner["access_token"]))
    user_id = uuid.UUID(me.json()["id"])

    step_up_token = security.create_step_up_token(user_id=user_id)
    # Presented as the ordinary bearer token, not via X-Step-Up-Token — must not be treated as a
    # general-purpose access token just because it decodes successfully.
    response = await client.get("/api/v1/auth/me", headers=auth_headers(step_up_token))
    assert response.status_code == 401


async def test_candidate_token_is_not_accepted_at_company_me(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="forge-candidate-at-company@example.com")
    response = await client.get("/api/v1/auth/me", headers=auth_headers(tokens["access_token"]))
    assert response.status_code == 401


async def test_company_token_is_not_accepted_at_candidate_me(client: AsyncClient) -> None:
    owner = await signup(client, email="forge-company-at-candidate@acme.com")
    response = await client.get(
        "/api/v1/candidate-auth/me", headers=auth_headers(owner["access_token"])
    )
    assert response.status_code == 401

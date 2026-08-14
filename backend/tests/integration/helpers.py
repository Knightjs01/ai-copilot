import re
import uuid

from httpx import AsyncClient

from app.modules.auth import security
from tests.conftest import CapturingEmailSender


async def signup(client: AsyncClient, *, email: str, company_name: str = "Acme Inc") -> dict:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "company_name": company_name,
            "email": email,
            "password": "correct horse battery staple",
            "full_name": "Ada Lovelace",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def step_up_headers(
    client: AsyncClient, *, headers: dict, password: str = "correct horse battery staple"
) -> dict:
    response = await client.post(
        "/api/v1/auth/step-up", json={"password": password}, headers=headers
    )
    assert response.status_code == 200, response.text
    return {**headers, "X-Step-Up-Token": response.json()["step_up_token"]}


async def candidate_signup(
    client: AsyncClient, *, email: str, full_name: str = "Jamie Candidate"
) -> dict:
    response = await client.post(
        "/api/v1/candidate-auth/signup",
        json={"email": email, "password": "correct horse battery staple", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def extract_token_from_email(sent_emails: CapturingEmailSender) -> str:
    for email in reversed(sent_emails.sent):
        match = re.search(r"token=([\w-]+)", email["body"])
        if match:
            return match.group(1)
    raise AssertionError("No token found in sent emails")


async def invite_and_accept(
    client: AsyncClient,
    *,
    inviter_headers: dict,
    email: str,
    role: str,
    sent_emails: CapturingEmailSender,
    inviter_password: str = "correct horse battery staple",
) -> dict:
    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": email, "full_name": "Invited Person", "role": role},
        headers=await step_up_headers(client, headers=inviter_headers, password=inviter_password),
    )
    assert invite_response.status_code == 201, invite_response.text
    token = extract_token_from_email(sent_emails)

    accept_response = await client.post(
        "/api/v1/users/accept-invite", json={"token": token, "password": "a secure password 123"}
    )
    assert accept_response.status_code == 200, accept_response.text
    return accept_response.json()


async def create_project(
    client: AsyncClient, *, headers: dict, title: str = "Test Project"
) -> dict:
    response = await client.post("/api/v1/projects", json={"title": title}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def forge_access_token(*, user_id: uuid.UUID, company_id: uuid.UUID) -> str:
    """Mints a real, validly-signed company access token for an arbitrary (user_id, company_id)
    pair — used by adversarial tests that need a token with attacker-chosen claims rather than
    whatever the signup/login flow would naturally issue. Same signing path production tokens go
    through (app.modules.auth.security.create_access_token); "forged" describes the caller's
    intent (mismatched claims), not the mechanism."""

    return security.create_access_token(user_id=user_id, company_id=company_id)


def forge_candidate_access_token(*, candidate_id: uuid.UUID) -> str:
    return security.create_candidate_access_token(candidate_id=candidate_id)

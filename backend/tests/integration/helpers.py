import re

from httpx import AsyncClient

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
) -> dict:
    invite_response = await client.post(
        "/api/v1/users/invite",
        json={"email": email, "full_name": "Invited Person", "role": role},
        headers=inviter_headers,
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

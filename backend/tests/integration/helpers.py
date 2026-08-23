import re
import uuid

from httpx import AsyncClient

from app.db.base import auth_session_factory
from app.modules.auth import security
from app.modules.company_access.service import CompanyAccessRequestService
from app.modules.platform_admin.repository import PlatformAdminRepository
from tests.conftest import CapturingEmailSender

_BOOTSTRAP_PLATFORM_ADMIN_EMAIL = "samuel@stormtalent.co.uk"
# Must match migration 0040_employer_access_gate.py's seeded bootstrap credential.
_BOOTSTRAP_PLATFORM_ADMIN_PASSWORD = "UFk-sS0NltqqNZK2oZs_kheB"


async def signup(client: AsyncClient, *, email: str, company_name: str = "Acme Inc") -> dict:
    """No public self-service company signup exists anymore -- this drives the real
    request -> approve -> login sequence (see company_access/__init__.py) and returns the exact
    same shape the old direct-signup endpoint used to, so none of this helper's ~300 existing
    call sites need to change. Approval goes through the service layer directly (not a full
    admin-HTTP round trip) purely for test-setup speed -- the admin HTTP flow itself gets its own
    dedicated coverage in test_company_access.py, so this shortcut doesn't leave the real gate
    untested."""

    password = "correct horse battery staple"
    request_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Ada Lovelace",
            "company_name": company_name,
            "work_email": email,
            "password": password,
        },
    )
    assert request_response.status_code == 201, request_response.text
    request_id = uuid.UUID(request_response.json()["id"])

    async with auth_session_factory() as session:
        admin = await PlatformAdminRepository(session).get_by_email(_BOOTSTRAP_PLATFORM_ADMIN_EMAIL)
        assert admin is not None, "bootstrap platform admin not seeded — check migration 0040"
        await CompanyAccessRequestService(session).approve_request(
            admin_id=admin.id, request_id=request_id
        )
        await session.commit()

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()


def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def platform_admin_headers(client: AsyncClient) -> dict:
    """Real HTTP login as the seeded bootstrap platform admin -- for tests that specifically
    need the admin-authenticated HTTP flow itself (e.g. to exercise get_email_sender's real
    dependency injection), as opposed to signup()'s service-layer shortcut."""

    response = await client.post(
        "/api/v1/platform-admin/login",
        json={
            "email": _BOOTSTRAP_PLATFORM_ADMIN_EMAIL,
            "password": _BOOTSTRAP_PLATFORM_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return auth_headers(response.json()["access_token"])


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
    # Kept as a single full_name kwarg so the ~40 existing call sites across this test suite
    # don't need to change -- split into first_name/last_name here, at the one real choke point,
    # to match the real signup schema.
    parts = full_name.split(" ", 1)
    first_name, last_name = parts[0], (parts[1] if len(parts) > 1 else None)
    response = await client.post(
        "/api/v1/candidate-auth/signup",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "first_name": first_name,
            "last_name": last_name,
        },
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

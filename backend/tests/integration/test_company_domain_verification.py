import uuid

from httpx import AsyncClient

from app.db.base import auth_session_factory
from app.modules.companies.repository import CompanyRepository
from tests.integration.helpers import auth_headers, signup, step_up_headers


async def _force_unverified_domain(client: AsyncClient, *, headers: dict) -> None:
    """Every company created via the real request/approve flow has a verified domain by
    construction now -- free-email domains are rejected at request time (see
    test_company_access.py::test_free_email_domain_is_rejected for that real coverage). This
    directly flips the flag to prove require_verified_domain's own gate still holds on its own
    terms, in case this state ever becomes reachable again (e.g. a future re-verification/
    downgrade path)."""

    me = await client.get("/api/v1/auth/me", headers=headers)
    async with auth_session_factory() as session:
        company = await CompanyRepository(session).get_by_id(uuid.UUID(me.json()["company_id"]))
        assert company is not None
        company.is_verified_domain = False
        await session.commit()


async def test_signup_with_corporate_domain_is_verified(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@realcompany.com", company_name="Real Company")
    headers = auth_headers(owner["access_token"])

    response = await client.get("/api/v1/companies/me", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email_domain"] == "realcompany.com"
    assert body["is_verified_domain"] is True


async def test_unverified_domain_blocked_from_inviting_teammates(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@unverifiedinvite.com", company_name="Unverified Co")
    headers = auth_headers(owner["access_token"])
    await _force_unverified_domain(client, headers=headers)

    response = await client.post(
        "/api/v1/users/invite",
        json={
            "email": "teammate@unverifiedinvite.com",
            "full_name": "Teammate",
            "role": "Recruiter",
        },
        headers=await step_up_headers(client, headers=headers),
    )
    assert response.status_code == 403


async def test_verified_domain_can_invite_teammates(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@verifiedco.com", company_name="Verified Co")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/users/invite",
        json={"email": "teammate@verifiedco.com", "full_name": "Teammate", "role": "Recruiter"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert response.status_code == 201, response.text


async def test_unverified_domain_blocked_from_publishing_shadow_job(client: AsyncClient) -> None:
    owner = await signup(
        client, email="owner@unverifiedshadow.com", company_name="Unverified Shadow Co"
    )
    headers = auth_headers(owner["access_token"])
    await _force_unverified_domain(client, headers=headers)

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own our core platform.",
            "description": "Full role description.",
        },
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job_id}/publish", headers=headers
    )
    assert publish_response.status_code == 403

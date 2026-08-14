from httpx import AsyncClient

from tests.integration.helpers import auth_headers, signup, step_up_headers


async def test_signup_with_corporate_domain_is_verified(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@realcompany.com", company_name="Real Company")
    headers = auth_headers(owner["access_token"])

    response = await client.get("/api/v1/companies/me", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email_domain"] == "realcompany.com"
    assert body["is_verified_domain"] is True


async def test_signup_with_free_email_domain_is_not_verified(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@gmail.com", company_name="Solo Recruiter")
    headers = auth_headers(owner["access_token"])

    response = await client.get("/api/v1/companies/me", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email_domain"] == "gmail.com"
    assert body["is_verified_domain"] is False


async def test_unverified_domain_blocked_from_inviting_teammates(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@yahoo.com", company_name="Unverified Co")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/users/invite",
        json={"email": "teammate@yahoo.com", "full_name": "Teammate", "role": "Member"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert response.status_code == 403


async def test_verified_domain_can_invite_teammates(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@verifiedco.com", company_name="Verified Co")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/users/invite",
        json={"email": "teammate@verifiedco.com", "full_name": "Teammate", "role": "Member"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert response.status_code == 201, response.text


async def test_unverified_domain_blocked_from_publishing_shadow_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@hotmail.com", company_name="Unverified Shadow Co")
    headers = auth_headers(owner["access_token"])

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

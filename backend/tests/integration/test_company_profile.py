from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, invite_and_accept, signup

_PROFILE_PAYLOAD = {
    "description": "We build tools for hiring teams.",
    "culture": "Remote-first, async by default.",
    "benefits": ["Private healthcare", "Unlimited PTO"],
    "size": "51-200",
    "industry": ["Software"],
    "is_profile_public": True,
}


async def test_owner_can_update_company_profile(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-owner.com")
    headers = auth_headers(owner["access_token"])

    response = await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["description"] == _PROFILE_PAYLOAD["description"]
    assert body["culture"] == _PROFILE_PAYLOAD["culture"]
    assert body["benefits"] == _PROFILE_PAYLOAD["benefits"]
    assert body["size"] == _PROFILE_PAYLOAD["size"]
    assert body["industry"] == _PROFILE_PAYLOAD["industry"]
    assert body["is_profile_public"] is True


async def test_member_cannot_update_company_profile(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@companyprofile-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@companyprofile-memberperm.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    response = await client.patch(
        "/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=member_headers
    )
    assert response.status_code == 403


async def test_public_profile_visible_when_opted_in(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-public.com")
    headers = auth_headers(owner["access_token"])
    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    response = await client.get(f"/api/v1/companies/{slug}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slug"] == slug
    assert body["description"] == _PROFILE_PAYLOAD["description"]
    assert "id" not in body
    assert "email_domain" not in body
    assert "is_verified_domain" not in body


async def test_public_profile_404_when_not_opted_in(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-private.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    response = await client.get(f"/api/v1/companies/{slug}")
    assert response.status_code == 404


async def test_public_profile_404_for_nonexistent_slug(client: AsyncClient) -> None:
    response = await client.get("/api/v1/companies/no-such-company")
    assert response.status_code == 404


async def test_board_listing_carries_company_slug_only_when_public(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-board.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Senior Backend Engineer",
            "summary": "Own our core platform services.",
            "description": "A full description of the role and its responsibilities.",
        },
        headers=headers,
    )
    job = job_response.json()
    publish = await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers)
    published = publish.json()

    board_before = await client.get("/api/v1/shadow-jobs/board")
    listing_before = next(j for j in board_before.json() if j["id"] == published["id"])
    assert listing_before["company_slug"] is None

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)

    board_after = await client.get("/api/v1/shadow-jobs/board")
    listing_after = next(j for j in board_after.json() if j["id"] == published["id"])
    assert listing_after["company_slug"] == slug

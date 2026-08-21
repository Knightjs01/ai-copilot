from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, invite_and_accept, signup, step_up_headers


async def test_recruiter_cannot_invite_but_ta_admin_can(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@perms.com", company_name="Perms Co")
    owner_headers = auth_headers(owner["access_token"])

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@perms.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])

    denied = await client.post(
        "/api/v1/users/invite",
        json={"email": "x@perms.com", "full_name": "X", "role": "Recruiter"},
        headers=recruiter_headers,
    )
    assert denied.status_code == 403

    can_view = await client.get("/api/v1/users", headers=recruiter_headers)
    assert can_view.status_code == 200

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@perms.com",
        role="TA Admin",
        sent_emails=sent_emails,
    )
    admin_headers = auth_headers(admin["access_token"])

    allowed = await client.post(
        "/api/v1/users/invite",
        json={"email": "y@perms.com", "full_name": "Y", "role": "Recruiter"},
        headers=await step_up_headers(
            client, headers=admin_headers, password="a secure password 123"
        ),
    )
    assert allowed.status_code == 201


async def test_cannot_invite_directly_as_owner(client: AsyncClient) -> None:
    owner = await signup(client, email="owner2@perms.com")
    owner_headers = auth_headers(owner["access_token"])
    response = await client.post(
        "/api/v1/users/invite",
        json={"email": "wannabe-owner@perms.com", "full_name": "X", "role": "Owner"},
        headers=await step_up_headers(client, headers=owner_headers),
    )
    assert response.status_code == 403


async def test_last_owner_cannot_be_removed(client: AsyncClient) -> None:
    owner = await signup(client, email="lastowner@perms.com")
    headers = auth_headers(owner["access_token"])

    me = await client.get("/api/v1/auth/me", headers=headers)
    owner_id = me.json()["id"]

    response = await client.delete(f"/api/v1/users/{owner_id}", headers=headers)
    assert response.status_code == 400


async def test_removed_user_loses_access(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="remover@perms.com", company_name="Remover Co")
    owner_headers = auth_headers(owner["access_token"])

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="removeme@perms.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    me_response = await client.get("/api/v1/auth/me", headers=member_headers)
    member_id = me_response.json()["id"]

    remove_response = await client.delete(f"/api/v1/users/{member_id}", headers=owner_headers)
    assert remove_response.status_code == 204

    still_listed = await client.get("/api/v1/users", headers=owner_headers)
    assert all(u["id"] != member_id for u in still_listed.json())

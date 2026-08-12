from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    create_project,
    invite_and_accept,
    signup,
    step_up_headers,
)


async def test_historic_vault_shows_purged_project_after_burn(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@histvault.com", company_name="Hist Vault Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Role To Purge")

    burn_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text

    response = await client.get("/api/v1/historic-vault", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["purged_project_count"] == 1
    record = data["purged_projects"][0]
    assert record["project_id"] == project["id"]
    assert record["project_title"] == "Role To Purge"
    assert record["candidate_count"] == 0
    assert "Candidate identity vault records" in record["data_categories_destroyed"]
    assert record["purged_by_email"] == "owner@histvault.com"
    assert record["purged_at"]


async def test_historic_vault_includes_burn_audit_entry(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@histvault-audit.com", company_name="Hist Audit Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Audited Role")

    burn_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200

    response = await client.get("/api/v1/historic-vault", headers=headers)
    assert response.status_code == 200, response.text
    entries = response.json()["recent_audit_entries"]

    matches = [
        e for e in entries if e["action"] == "project.burned" and e["target_id"] == project["id"]
    ]
    assert len(matches) == 1
    assert matches[0]["actor_email"] == "owner@histvault-audit.com"
    assert matches[0]["extra_data"]["title"] == "Audited Role"


async def test_historic_vault_requires_admin_or_owner(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@histvault-perms.com", company_name="Hist Perms Co")
    owner_headers = auth_headers(owner["access_token"])

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@histvault-perms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])
    denied_response = await client.get("/api/v1/historic-vault", headers=member_headers)
    assert denied_response.status_code == 403

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@histvault-perms.com",
        role="Admin",
        sent_emails=sent_emails,
    )
    admin_headers = auth_headers(admin["access_token"])
    allowed_response = await client.get("/api/v1/historic-vault", headers=admin_headers)
    assert allowed_response.status_code == 200


async def test_historic_vault_is_scoped_to_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@histvault-tenant-a.com", company_name="Hist A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a, title="Tenant A Role")
    burn_response = await client.post(
        f"/api/v1/projects/{project_a['id']}/burn",
        headers=await step_up_headers(client, headers=headers_a),
    )
    assert burn_response.status_code == 200

    owner_b = await signup(client, email="owner@histvault-tenant-b.com", company_name="Hist B")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get("/api/v1/historic-vault", headers=headers_b)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["purged_project_count"] == 0
    assert data["purged_projects"] == []
    assert all(e["target_id"] != project_a["id"] for e in data["recent_audit_entries"])

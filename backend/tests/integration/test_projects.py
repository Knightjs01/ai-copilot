from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, invite_and_accept, signup


async def test_project_crud_happy_path(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@projects.com", company_name="Projects Co")
    headers = auth_headers(owner["access_token"])

    create_response = await client.post(
        "/api/v1/projects",
        json={"title": "Senior Backend Engineer", "department": "Engineering"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    project = create_response.json()
    assert project["title"] == "Senior Backend Engineer"
    assert project["status"] == "draft"

    list_response = await client.get("/api/v1/projects", headers=headers)
    assert list_response.status_code == 200
    assert any(p["id"] == project["id"] for p in list_response.json())

    get_response = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Senior Backend Engineer"

    update_response = await client.patch(
        f"/api/v1/projects/{project['id']}", json={"status": "open"}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "open"

    delete_response = await client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert delete_response.status_code == 204

    after_delete = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert after_delete.status_code == 404


async def test_member_can_view_but_not_create_update_delete_projects(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@projperms.com", company_name="ProjPerms Co")
    owner_headers = auth_headers(owner["access_token"])

    create_response = await client.post(
        "/api/v1/projects", json={"title": "Product Designer"}, headers=owner_headers
    )
    project_id = create_response.json()["id"]

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@projperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    view_response = await client.get("/api/v1/projects", headers=member_headers)
    assert view_response.status_code == 200

    create_denied = await client.post(
        "/api/v1/projects", json={"title": "Should Fail"}, headers=member_headers
    )
    assert create_denied.status_code == 403

    update_denied = await client.patch(
        f"/api/v1/projects/{project_id}", json={"status": "open"}, headers=member_headers
    )
    assert update_denied.status_code == 403

    delete_denied = await client.delete(f"/api/v1/projects/{project_id}", headers=member_headers)
    assert delete_denied.status_code == 403


async def test_hiring_manager_must_belong_to_same_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@companya.com", company_name="Company A")
    headers_a = auth_headers(owner_a["access_token"])

    owner_b = await signup(client, email="owner@companyb.com", company_name="Company B")
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(owner_b["access_token"]))
    owner_b_id = me_b.json()["id"]

    response = await client.post(
        "/api/v1/projects",
        json={"title": "Cross-company Manager", "hiring_manager_id": owner_b_id},
        headers=headers_a,
    )
    assert response.status_code == 400


async def test_rls_blocks_cross_tenant_project_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsproj-a.com", company_name="RLS Proj A")
    headers_a = auth_headers(owner_a["access_token"])
    await client.post("/api/v1/projects", json={"title": "Company A Project"}, headers=headers_a)

    owner_b = await signup(client, email="owner@rlsproj-b.com", company_name="RLS Proj B")
    me_a = await client.get("/api/v1/auth/me", headers=headers_a)
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(owner_b["access_token"]))
    company_a_id = me_a.json()["company_id"]
    company_b_id = me_b.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            import uuid as uuid_module

            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_a_id)}'")
            )
            explicit_cross_tenant_query = await conn.execute(
                text("SELECT id FROM projects WHERE company_id = :cid"), {"cid": company_b_id}
            )
            assert explicit_cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_projects() -> None:
    """Proves the Phase 2 migration's default-privileges fix actually took effect — app_auth
    should be unable to touch `projects` at all, not just see zero rows via RLS."""

    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM projects LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on projects"
    finally:
        await auth_engine.dispose()

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup

_TOP_REQUIREMENTS = [
    "5+ years Python backend experience",
    "Distributed systems design",
    "Track record mentoring engineers",
    "Strong communication skills",
    "Startup/scale-up experience",
]


async def test_submit_alignment_happy_path(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@alignment.com", company_name="Alignment Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": _TOP_REQUIREMENTS},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    alignment = response.json()
    assert alignment["top_requirements"] == _TOP_REQUIREMENTS
    assert alignment["project_id"] == project["id"]

    get_response = await client.get(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["top_requirements"] == _TOP_REQUIREMENTS


async def test_resubmitting_overwrites_previous_alignment(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@resubmit.com", company_name="Resubmit Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    first = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["Requirement A"]},
        headers=headers,
    )
    assert first.status_code == 200

    second = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["Requirement B", "Requirement C"]},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["top_requirements"] == ["Requirement B", "Requirement C"]


async def test_submit_alignment_rejects_empty_and_oversized_lists(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@alignmentvalidation.com", company_name="Val Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    empty_response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": []},
        headers=headers,
    )
    assert empty_response.status_code == 422

    oversized_response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["1", "2", "3", "4", "5", "6"]},
        headers=headers,
    )
    assert oversized_response.status_code == 422


async def test_member_can_view_but_not_submit_alignment(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@alignmentperms.com", company_name="Align Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers)
    await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": _TOP_REQUIREMENTS},
        headers=owner_headers,
    )

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@alignmentperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    submit_denied = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["Should fail"]},
        headers=member_headers,
    )
    assert submit_denied.status_code == 403

    view_allowed = await client.get(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment", headers=member_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_alignment_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsalign-a.com", company_name="RLS Align A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a)
    await client.put(
        f"/api/v1/projects/{project_a['id']}/hiring-manager-alignment",
        json={"top_requirements": _TOP_REQUIREMENTS},
        headers=headers_a,
    )

    owner_b = await signup(client, email="owner@rlsalign-b.com", company_name="RLS Align B")
    me_a = await client.get("/api/v1/auth/me", headers=headers_a)
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(owner_b["access_token"]))
    company_a_id = me_a.json()["company_id"]
    company_b_id = me_b.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            import uuid as uuid_module

            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_b_id)}'")
            )
            cross_tenant_query = await conn.execute(
                text("SELECT id FROM hiring_manager_alignments WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_hiring_manager_alignments() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM hiring_manager_alignments LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on hiring_manager_alignments"
    finally:
        await auth_engine.dispose()

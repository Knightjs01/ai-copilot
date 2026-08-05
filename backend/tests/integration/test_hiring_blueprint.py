from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender, FakeHiringBlueprintLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


async def _create_project_with_role_brief(
    client: AsyncClient, *, headers: dict, role_brief: str
) -> str:
    project = await create_project(client, headers=headers, title="Senior Backend Engineer")
    patch_response = await client.patch(
        f"/api/v1/projects/{project['id']}", json={"role_brief": role_brief}, headers=headers
    )
    assert patch_response.status_code == 200, patch_response.text
    return project["id"]


async def test_generate_hiring_blueprint_happy_path(
    client: AsyncClient, fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient
) -> None:
    owner = await signup(client, email="owner@blueprint.com", company_name="Blueprint Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_role_brief(
        client,
        headers=headers,
        role_brief="Looking for a senior backend engineer to lead our platform team.",
    )

    generate_response = await client.post(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers
    )
    assert generate_response.status_code == 200, generate_response.text
    blueprint = generate_response.json()

    assert blueprint["role_summary"] == "A fake but deterministic role summary for testing."
    assert blueprint["key_responsibilities"] == ["Build things", "Review code"]
    assert blueprint["must_have_qualifications"] == ["Fake required skill"]
    assert blueprint["nice_to_have_qualifications"] == ["Fake bonus skill"]
    assert blueprint["evaluation_criteria"] == ["Technical depth", "Collaboration"]
    assert blueprint["model_used"] == "claude-sonnet-5"

    assert len(fake_hiring_blueprint_llm_client.calls) == 1
    assert "senior backend engineer" in fake_hiring_blueprint_llm_client.calls[0]

    get_response = await client.get(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == blueprint["id"]


async def test_generate_without_role_brief_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@norolebrief.com", company_name="No Brief Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.post(
        f"/api/v1/projects/{project['id']}/hiring-blueprint", headers=headers
    )
    assert response.status_code == 400  # MissingRoleBriefError


async def test_member_can_view_but_not_trigger_generation(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@blueprintperms.com", company_name="Blueprint Perms")
    owner_headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_role_brief(
        client, headers=owner_headers, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/hiring-blueprint", headers=owner_headers)

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@blueprintperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    generate_denied = await client.post(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=member_headers
    )
    assert generate_denied.status_code == 403

    view_allowed = await client.get(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=member_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_hiring_blueprint_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsblueprint-a.com", company_name="RLS Bp A")
    headers_a = auth_headers(owner_a["access_token"])
    project_id = await _create_project_with_role_brief(
        client, headers=headers_a, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers_a)

    owner_b = await signup(client, email="owner@rlsblueprint-b.com", company_name="RLS Bp B")
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
                text("SELECT id FROM hiring_blueprints WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_hiring_blueprints() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM hiring_blueprints LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on hiring_blueprints"
    finally:
        await auth_engine.dispose()

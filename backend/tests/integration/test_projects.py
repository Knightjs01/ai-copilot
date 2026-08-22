from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


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
        role="Recruiter",
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


async def test_member_only_sees_projects_they_are_a_member_of(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@resourcescope.com", company_name="ResourceScope Co")
    owner_headers = auth_headers(owner["access_token"])

    assigned = await create_project(client, headers=owner_headers, title="Assigned Project")
    unassigned = await create_project(client, headers=owner_headers, title="Unassigned Project")

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@resourcescope.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])
    member_id = (await client.get("/api/v1/auth/me", headers=member_headers)).json()["id"]

    # Not a member of either project yet — the list is empty and direct access 404s (not 403 —
    # a Member should not be able to tell "doesn't exist" apart from "not assigned to me").
    list_before = await client.get("/api/v1/projects", headers=member_headers)
    assert list_before.json() == []
    get_before = await client.get(f"/api/v1/projects/{assigned['id']}", headers=member_headers)
    assert get_before.status_code == 404

    add_response = await client.post(
        f"/api/v1/projects/{assigned['id']}/members",
        json={"user_id": member_id},
        headers=owner_headers,
    )
    assert add_response.status_code == 201, add_response.text

    list_after = await client.get("/api/v1/projects", headers=member_headers)
    ids_after = {p["id"] for p in list_after.json()}
    assert ids_after == {assigned["id"]}

    get_after = await client.get(f"/api/v1/projects/{assigned['id']}", headers=member_headers)
    assert get_after.status_code == 200

    still_blocked = await client.get(f"/api/v1/projects/{unassigned['id']}", headers=member_headers)
    assert still_blocked.status_code == 404

    # Candidates inherit the same scoping through their project.
    candidate_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": assigned["id"], "full_name": "Scoped Candidate"},
        headers=owner_headers,
    )
    assert candidate_response.status_code == 201, candidate_response.text
    candidate_id = candidate_response.json()["id"]

    unassigned_candidate_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": unassigned["id"], "full_name": "Unscoped Candidate"},
        headers=owner_headers,
    )
    unassigned_candidate_id = unassigned_candidate_response.json()["id"]

    candidate_get = await client.get(f"/api/v1/candidates/{candidate_id}", headers=member_headers)
    assert candidate_get.status_code == 200

    other_candidate_get = await client.get(
        f"/api/v1/candidates/{unassigned_candidate_id}", headers=member_headers
    )
    assert other_candidate_get.status_code == 404

    # Recruiter (unlike the old Member) has real candidates.create permission but isn't
    # org-wide, so the role check in require_permission passes and it's create_candidate's own
    # project-membership check that actually blocks this — the exact defense-in-depth scenario
    # this check exists for. 404, not 403: a Recruiter shouldn't be able to tell "doesn't exist"
    # apart from "not assigned to me."
    create_in_unassigned = await client.post(
        "/api/v1/candidates",
        json={"project_id": unassigned["id"], "full_name": "Should Fail"},
        headers=member_headers,
    )
    assert create_in_unassigned.status_code == 404

    remove_response = await client.delete(
        f"/api/v1/projects/{assigned['id']}/members/{member_id}", headers=owner_headers
    )
    assert remove_response.status_code == 204

    get_after_removal = await client.get(
        f"/api/v1/projects/{assigned['id']}", headers=member_headers
    )
    assert get_after_removal.status_code == 404


async def test_owner_and_admin_bypass_project_membership_scoping(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@orgwide.com", company_name="OrgWide Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers, title="No Members Added")

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@orgwide.com",
        role="TA Admin",
        sent_emails=sent_emails,
    )
    admin_headers = auth_headers(admin["access_token"])

    # Admin was never added as a ProjectMember of this project (only the Owner, its creator, is
    # a member) — Admin's org-wide role bypass means it sees it company-wide anyway.
    get_as_admin = await client.get(f"/api/v1/projects/{project['id']}", headers=admin_headers)
    assert get_as_admin.status_code == 200

    list_as_admin = await client.get("/api/v1/projects", headers=admin_headers)
    assert any(p["id"] == project["id"] for p in list_as_admin.json())


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


async def test_project_activity_feed_scoped_to_this_project(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@project-activity.com", company_name="Activity Co")
    headers = auth_headers(owner["access_token"])

    project_a = await create_project(client, headers=headers, title="Role A")
    project_b = await create_project(client, headers=headers, title="Role B")

    await client.patch(
        f"/api/v1/projects/{project_a['id']}", json={"status": "open"}, headers=headers
    )
    await client.patch(
        f"/api/v1/projects/{project_b['id']}", json={"status": "open"}, headers=headers
    )

    response = await client.get(f"/api/v1/projects/{project_a['id']}/activity", headers=headers)
    assert response.status_code == 200, response.text
    entries = response.json()
    assert len(entries) >= 1
    assert all("id" in e and "action" in e and "created_at" in e for e in entries)
    # Newest first.
    assert entries == sorted(entries, key=lambda e: e["created_at"], reverse=True)


async def test_project_activity_feed_cross_tenant_isolation(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner-a@project-activity-iso.com")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a, title="Role A")

    owner_b = await signup(client, email="owner-b@project-activity-iso-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get(f"/api/v1/projects/{project_a['id']}/activity", headers=headers_b)
    assert response.status_code == 404


async def test_role_fields_round_trip_and_clear_to_null(client: AsyncClient) -> None:
    """AI Role Intake: seniority/location/salary_min/salary_max round-trip through PATCH, and
    -- unlike department/role_brief, which can only ever be set, never cleared -- these four
    get real tri-state semantics (an explicit null in the request body clears the field), since
    they're LLM-suggested-then-user-edited values where "clear a wrong AI guess" is a real,
    expected action."""
    owner = await signup(client, email="owner@rolefields.com", company_name="Role Fields Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    set_response = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={
            "seniority": "Senior",
            "location": "Remote (UK)",
            "salary_min": 90000,
            "salary_max": 110000,
        },
        headers=headers,
    )
    assert set_response.status_code == 200, set_response.text
    saved = set_response.json()
    assert saved["seniority"] == "Senior"
    assert saved["location"] == "Remote (UK)"
    assert saved["salary_min"] == 90000
    assert saved["salary_max"] == 110000

    # Explicit null clears -- a wrong AI-suggested salary is a real thing to clear.
    clear_response = await client.patch(
        f"/api/v1/projects/{project['id']}", json={"salary_min": None}, headers=headers
    )
    assert clear_response.status_code == 200, clear_response.text
    cleared = clear_response.json()
    assert cleared["salary_min"] is None
    # Fields not present in this PATCH's body are left alone, not silently cleared.
    assert cleared["seniority"] == "Senior"
    assert cleared["location"] == "Remote (UK)"
    assert cleared["salary_max"] == 110000

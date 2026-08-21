from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup

_FAKE_PDF_CONTENT = b"%PDF-1.4 fake resume content for testing purposes only"


async def test_candidate_crud_happy_path(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@candidates.com", company_name="Candidates Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={
            "project_id": project["id"],
            "full_name": "Jane Applicant",
            "email": "jane@example.com",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    candidate = create_response.json()
    assert "full_name" not in candidate
    assert "email" not in candidate
    assert candidate["callsign"]
    assert candidate["candidate_ref"].startswith("PH-")
    assert candidate["status"] == "new"

    list_response = await client.get(
        "/api/v1/candidates", params={"project_id": project["id"]}, headers=headers
    )
    assert list_response.status_code == 200
    assert any(c["id"] == candidate["id"] for c in list_response.json())

    get_response = await client.get(f"/api/v1/candidates/{candidate['id']}", headers=headers)
    assert get_response.status_code == 200

    update_response = await client.patch(
        f"/api/v1/candidates/{candidate['id']}", json={"status": "screening"}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "screening"

    delete_response = await client.delete(f"/api/v1/candidates/{candidate['id']}", headers=headers)
    assert delete_response.status_code == 204

    after_delete = await client.get(f"/api/v1/candidates/{candidate['id']}", headers=headers)
    assert after_delete.status_code == 404


async def test_recruiter_can_create_update_but_not_delete_candidates(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Recruiter (renamed + permission-expanded from the old Member) gets real create/update
    rights once added to the project -- unlike old Member, which was view-only. Deletion stays
    Owner/TA Admin only regardless of project membership."""
    owner = await signup(client, email="owner@candperms.com", company_name="CandPerms Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Existing Candidate"},
        headers=owner_headers,
    )
    candidate_id = create_response.json()["id"]

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@candperms.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])
    me_response = await client.get("/api/v1/auth/me", headers=recruiter_headers)
    recruiter_id = me_response.json()["id"]

    # Not yet a project member -- create is permission-allowed but resource-scope blocks it.
    create_before_membership = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Too Early"},
        headers=recruiter_headers,
    )
    assert create_before_membership.status_code == 404

    add_member_response = await client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"user_id": recruiter_id},
        headers=owner_headers,
    )
    assert add_member_response.status_code == 201, add_member_response.text

    view_response = await client.get("/api/v1/candidates", headers=recruiter_headers)
    assert view_response.status_code == 200

    create_allowed = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "New Candidate"},
        headers=recruiter_headers,
    )
    assert create_allowed.status_code == 201, create_allowed.text

    update_allowed = await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={"status": "screening"},
        headers=recruiter_headers,
    )
    assert update_allowed.status_code == 200, update_allowed.text
    assert update_allowed.json()["status"] == "screening"

    delete_denied = await client.delete(
        f"/api/v1/candidates/{candidate_id}", headers=recruiter_headers
    )
    assert delete_denied.status_code == 403


async def test_update_candidate_prescreen_fields(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@prescreenfields.com", company_name="Prescreen Fields")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Prescreen Fields Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]
    assert create_response.json()["interview_scheduled_at"] is None
    assert create_response.json()["prescreen_outcome"] is None
    assert create_response.json()["prescreen_notes"] is None
    assert create_response.json()["expected_salary"] is None
    assert create_response.json()["agency_name"] is None
    assert create_response.json()["notice_period"] is None

    update_response = await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={
            "interview_scheduled_at": "2026-09-01T14:00:00Z",
            "prescreen_outcome": "advance",
            "prescreen_notes": "Strong communicator, advancing to hiring manager round.",
            "expected_salary": 95000,
            "agency_name": "Talent Partners",
            "notice_period": "one_month",
        },
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["interview_scheduled_at"] == "2026-09-01T14:00:00Z"
    assert updated["prescreen_outcome"] == "advance"
    assert updated["prescreen_notes"] == "Strong communicator, advancing to hiring manager round."
    assert updated["expected_salary"] == 95000
    assert updated["agency_name"] == "Talent Partners"
    assert updated["notice_period"] == "one_month"


async def test_project_id_must_belong_to_same_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@companya2.com", company_name="Company A2")
    headers_a = auth_headers(owner_a["access_token"])

    owner_b = await signup(client, email="owner@companyb2.com", company_name="Company B2")
    headers_b = auth_headers(owner_b["access_token"])
    project_b = await create_project(client, headers=headers_b)

    response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_b["id"], "full_name": "Cross Company Candidate"},
        headers=headers_a,
    )
    assert response.status_code == 404


async def test_resume_upload_and_download_roundtrip(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@resumes.com", company_name="Resumes Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Resume Owner"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.pdf", _FAKE_PDF_CONTENT, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text
    assert upload_response.json()["resume_original_filename"] == "resume.pdf"

    download_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/resume", headers=headers
    )
    assert download_response.status_code == 200
    assert download_response.content == _FAKE_PDF_CONTENT


async def test_resume_upload_rejects_oversized_file(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@oversized.com", company_name="Oversized Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Big File Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    oversized_content = b"x" * (11 * 1024 * 1024)  # 11MB, over the 10MB default limit
    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("huge.pdf", oversized_content, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400


async def test_resume_upload_rejects_disallowed_content_type(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@wrongtype.com", company_name="WrongType Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Wrong Type Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.exe", b"not a resume", "application/x-msdownload")},
        headers=headers,
    )
    assert response.status_code == 400


async def test_rls_blocks_cross_tenant_candidate_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlscand-a.com", company_name="RLS Cand A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a)
    await client.post(
        "/api/v1/candidates",
        json={"project_id": project_a["id"], "full_name": "Company A Candidate"},
        headers=headers_a,
    )

    owner_b = await signup(client, email="owner@rlscand-b.com", company_name="RLS Cand B")
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
                text("SELECT id FROM candidates WHERE company_id = :cid"), {"cid": company_b_id}
            )
            assert explicit_cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_candidates() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM candidates LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on candidates"
    finally:
        await auth_engine.dispose()


async def test_list_candidates_across_projects(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Phantom ATS UX redesign, Phase 1 (Pipeline view): GET /candidates with no project_id
    already returns candidates across every accessible project, not just one -- this pins that
    behavior down explicitly at a higher limit, and confirms org-wide vs. project-scoped actors
    still see the correct, different slices."""
    owner = await signup(client, email="owner@pipeline.com", company_name="Pipeline Co")
    owner_headers = auth_headers(owner["access_token"])
    project_a = await create_project(client, headers=owner_headers, title="Role A")
    project_b = await create_project(client, headers=owner_headers, title="Role B")

    candidate_a = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_a["id"], "full_name": "Candidate A"},
        headers=owner_headers,
    )
    assert candidate_a.status_code == 201, candidate_a.text
    candidate_b = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_b["id"], "full_name": "Candidate B"},
        headers=owner_headers,
    )
    assert candidate_b.status_code == 201, candidate_b.text

    # Org-wide actor (Owner): sees both, across both projects, in one call.
    owner_list = await client.get(
        "/api/v1/candidates", params={"limit": 500}, headers=owner_headers
    )
    assert owner_list.status_code == 200
    owner_ids = {c["id"] for c in owner_list.json()}
    assert candidate_a.json()["id"] in owner_ids
    assert candidate_b.json()["id"] in owner_ids

    # Scoped Recruiter, added only to project A: sees only project A's candidate.
    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@pipeline.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])
    me_response = await client.get("/api/v1/auth/me", headers=recruiter_headers)
    recruiter_id = me_response.json()["id"]
    add_member_response = await client.post(
        f"/api/v1/projects/{project_a['id']}/members",
        json={"user_id": recruiter_id},
        headers=owner_headers,
    )
    assert add_member_response.status_code == 201, add_member_response.text

    recruiter_list = await client.get(
        "/api/v1/candidates", params={"limit": 500}, headers=recruiter_headers
    )
    assert recruiter_list.status_code == 200
    recruiter_ids = {c["id"] for c in recruiter_list.json()}
    assert candidate_a.json()["id"] in recruiter_ids
    assert candidate_b.json()["id"] not in recruiter_ids

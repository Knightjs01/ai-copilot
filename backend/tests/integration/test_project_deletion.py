import uuid as uuid_module

from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text

from app.modules.candidates.storage import EncryptingFileStorage
from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    candidate_signup,
    create_project,
    invite_and_accept,
    signup,
    step_up_headers,
)


def _build_resume_pdf(*, full_name: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(w=0, text=f"{full_name}\nBackend engineer with Python and SQL experience.")
    return bytes(pdf.output())


async def _setup_project_with_blueprint_and_alignment(client: AsyncClient, *, headers: dict) -> str:
    project = await create_project(client, headers=headers, title="Senior Backend Engineer")
    project_id = project["id"]

    patch_response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"role_brief": "Looking for a senior backend engineer."},
        headers=headers,
    )
    assert patch_response.status_code == 200

    blueprint_response = await client.post(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers
    )
    assert blueprint_response.status_code == 200

    kit_response = await client.post(
        f"/api/v1/projects/{project_id}/interview-kit", headers=headers
    )
    assert kit_response.status_code == 200

    alignment_response = await client.put(
        f"/api/v1/projects/{project_id}/hiring-manager-alignment",
        json={"top_requirements": ["5+ years Python"]},
        headers=headers,
    )
    assert alignment_response.status_code == 200

    return project_id


async def _get_resume_file_key(company_id: str, candidate_id: str) -> str | None:
    from app.db.base import engine

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            result = await conn.execute(
                text("SELECT resume_file_key FROM candidates WHERE id = :id"),
                {"id": candidate_id},
            )
            row = result.fetchone()
            return row[0] if row else None


async def _table_row_count(table: str, column: str, value: str, *, company_id: str) -> int:
    # app.db.base.engine connects as app_runtime (RLS-enforced, no BYPASSRLS) — every affected
    # table has a tenant_isolation policy, so without SET LOCAL this would silently see zero
    # rows for every query regardless of actual state.
    from app.db.base import engine

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE {column} = :value"),  # noqa: S608
                {"value": value},
            )
            return result.scalar_one()


async def test_burn_project_purges_everything(
    client: AsyncClient, test_storage: EncryptingFileStorage
) -> None:
    owner = await signup(client, email="owner@burn.com", company_name="Burn Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]

    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)

    # Candidate A: resume uploaded but never sanitized — resume_file_key still set, exercises
    # the file-cleanup path.
    candidate_a = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": "Candidate Unsanitized"},
        headers=headers,
    )
    candidate_a_id = candidate_a.json()["id"]
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_a_id}/resume",
        files={
            "file": ("resume.pdf", _build_resume_pdf(full_name="Candidate A"), "application/pdf")
        },
        headers=headers,
    )
    assert upload_response.status_code == 200
    resume_key = await _get_resume_file_key(company_id, candidate_a_id)
    assert resume_key is not None
    # Sanity check the file really is there before we burn anything.
    await test_storage.read(key=resume_key)

    # Candidate B: taken all the way through intelligence pack + prescreen assessment, exercises
    # the full cross-table purge.
    candidate_b = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": "Candidate Fully Processed"},
        headers=headers,
    )
    candidate_b_id = candidate_b.json()["id"]
    await client.post(
        f"/api/v1/candidates/{candidate_b_id}/resume",
        files={
            "file": ("resume.pdf", _build_resume_pdf(full_name="Candidate B"), "application/pdf")
        },
        headers=headers,
    )
    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate_b_id}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 200
    pack_response = await client.post(
        f"/api/v1/candidates/{candidate_b_id}/intelligence-pack", headers=headers
    )
    assert pack_response.status_code == 200
    assessment_response = await client.post(
        f"/api/v1/candidates/{candidate_b_id}/prescreen-assessment", headers=headers
    )
    assert assessment_response.status_code == 200

    # Everything exists before the burn.
    assert (
        await _table_row_count("candidates", "project_id", project_id, company_id=company_id) == 2
    )
    assert (
        await _table_row_count("hiring_blueprints", "project_id", project_id, company_id=company_id)
        == 1
    )
    assert (
        await _table_row_count("interview_kits", "project_id", project_id, company_id=company_id)
        == 1
    )
    assert (
        await _table_row_count(
            "hiring_manager_alignments", "project_id", project_id, company_id=company_id
        )
        == 1
    )
    assert (
        await _table_row_count(
            "sanitized_profiles", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 1
    )
    assert (
        await _table_row_count(
            "intelligence_packs", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 1
    )
    assert (
        await _table_row_count(
            "prescreen_assessments", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 1
    )
    assert (
        await _table_row_count(
            "candidate_identity_vaults", "candidate_id", candidate_a_id, company_id=company_id
        )
        == 1
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text
    body = burn_response.json()
    assert body["candidate_count"] == 2
    certificate = body["certificate"]
    assert certificate["candidate_count"] == 2
    assert "Candidate identity vault records" in certificate["data_categories_destroyed"]
    assert "Identity reveal audit trail" in certificate["data_categories_destroyed"]

    # Nothing survives the burn.
    assert await _table_row_count("projects", "id", project_id, company_id=company_id) == 0
    assert (
        await _table_row_count("candidates", "project_id", project_id, company_id=company_id) == 0
    )
    assert (
        await _table_row_count("hiring_blueprints", "project_id", project_id, company_id=company_id)
        == 0
    )
    assert (
        await _table_row_count("interview_kits", "project_id", project_id, company_id=company_id)
        == 0
    )
    assert (
        await _table_row_count(
            "hiring_manager_alignments", "project_id", project_id, company_id=company_id
        )
        == 0
    )
    assert (
        await _table_row_count(
            "sanitized_profiles", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 0
    )
    assert (
        await _table_row_count(
            "intelligence_packs", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 0
    )
    assert (
        await _table_row_count(
            "prescreen_assessments", "candidate_id", candidate_b_id, company_id=company_id
        )
        == 0
    )
    assert (
        await _table_row_count(
            "candidate_identity_vaults", "candidate_id", candidate_a_id, company_id=company_id
        )
        == 0
    )

    # The resume file itself is gone from storage, not just dereferenced.
    try:
        await test_storage.read(key=resume_key)
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised, "resume file should have been deleted from storage"

    # The project itself is unreachable now.
    get_project_response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_project_response.status_code == 404


async def test_burn_project_audit_entry_survives(client: AsyncClient) -> None:
    from app.db.base import engine

    owner = await signup(client, email="owner@burnaudit.com", company_name="Burn Audit Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Role To Burn")
    project_id = project["id"]

    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200
    body = burn_response.json()
    assert body["candidate_count"] == 0
    assert body["certificate"]["project_title"] == "Role To Burn"
    assert body["certificate"]["candidate_count"] == 0
    assert body["certificate"]["purged_at"]

    async with engine.connect() as conn:
        async with conn.begin():
            # audit_logs is RLS-backed (Security: close RLS coverage gap) — needs the company
            # context set, same as every other RLS-scoped table this suite queries directly.
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            result = await conn.execute(
                text(
                    "SELECT metadata FROM audit_logs "
                    "WHERE action = 'project.burned' AND target_id = :id"
                ),
                {"id": project_id},
            )
            row = result.fetchone()
            assert row is not None, "audit entry should survive even though the project is gone"
            assert row[0]["title"] == "Role To Burn"
            assert row[0]["candidate_count"] == 0


async def test_burn_project_requires_projects_delete_permission(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@burnperms.com", company_name="Burn Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers)

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@burnperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    denied_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn", headers=member_headers
    )
    assert denied_response.status_code == 403

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@burnperms.com",
        role="Admin",
        sent_emails=sent_emails,
    )
    admin_headers = auth_headers(admin["access_token"])
    allowed_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(
            client, headers=admin_headers, password="a secure password 123"
        ),
    )
    assert allowed_response.status_code == 200


async def test_burn_project_cross_tenant_fails(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@burntenant-a.com", company_name="Burn Tenant A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a)

    owner_b = await signup(client, email="owner@burntenant-b.com", company_name="Burn Tenant B")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.post(
        f"/api/v1/projects/{project_a['id']}/burn",
        headers=await step_up_headers(client, headers=headers_b),
    )
    assert response.status_code == 404

    # Company A's project must be untouched.
    still_there = await client.get(f"/api/v1/projects/{project_a['id']}", headers=headers_a)
    assert still_there.status_code == 200


async def test_burn_project_purges_linked_shadow_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@burnshadow.com", company_name="Burn Shadow Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers, title="Role With Shadow Job")
    project_id = project["id"]

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own our core platform.",
            "description": "Full role description.",
            "project_id": project_id,
        },
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job_id}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text

    candidate_tokens = await candidate_signup(client, email="applicant@burnshadow.com")
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    passport_response = await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Staff Engineer",
            "personal_info": {"legal_name": "Shadow Applicant"},
            "career_entries": [],
        },
        headers=candidate_headers,
    )
    assert passport_response.status_code == 200, passport_response.text
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job_id}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    application_id = apply_response.json()["id"]

    reveal_request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job_id}/applicants/{application_id}/request",
        json={},
        headers=headers,
    )
    assert reveal_request_response.status_code == 201, reveal_request_response.text

    assert await _table_row_count("shadow_jobs", "id", job_id, company_id=company_id) == 1
    assert (
        await _table_row_count(
            "shadow_applications", "shadow_job_id", job_id, company_id=company_id
        )
        == 1
    )
    assert (
        await _table_row_count(
            "shadow_reveal_requests", "shadow_application_id", application_id, company_id=company_id
        )
        == 1
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text
    categories = burn_response.json()["certificate"]["data_categories_destroyed"]
    assert "Shadow job board listing and applicants" in categories
    assert "Identity reveal requests and audit trail" in categories

    assert await _table_row_count("shadow_jobs", "id", job_id, company_id=company_id) == 0
    assert (
        await _table_row_count(
            "shadow_applications", "shadow_job_id", job_id, company_id=company_id
        )
        == 0
    )
    assert (
        await _table_row_count(
            "shadow_reveal_requests", "shadow_application_id", application_id, company_id=company_id
        )
        == 0
    )


async def test_burn_project_without_shadow_job_omits_shadow_categories(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@burnnoshadowjob.com")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    burn_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text
    categories = burn_response.json()["certificate"]["data_categories_destroyed"]
    assert "Shadow job board listing and applicants" not in categories


async def test_burn_already_soft_deleted_project(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@burnsoftdeleted.com", company_name="Soft Del Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers)

    delete_response = await client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert delete_response.status_code == 204

    burn_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200
    assert await _table_row_count("projects", "id", project["id"], company_id=company_id) == 0

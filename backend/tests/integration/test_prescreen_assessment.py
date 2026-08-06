from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender, FakePrescreenAssessmentLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


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
    assert patch_response.status_code == 200, patch_response.text

    blueprint_response = await client.post(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers
    )
    assert blueprint_response.status_code == 200, blueprint_response.text

    alignment_response = await client.put(
        f"/api/v1/projects/{project_id}/hiring-manager-alignment",
        json={"top_requirements": ["5+ years Python", "Distributed systems experience"]},
        headers=headers,
    )
    assert alignment_response.status_code == 200, alignment_response.text

    return project_id


async def _create_candidate_with_intelligence_pack(
    client: AsyncClient, *, headers: dict, project_id: str, full_name: str
) -> str:
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": full_name},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    resume_bytes = _build_resume_pdf(full_name=full_name)
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.pdf", resume_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text

    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 200, sanitize_response.text

    pack_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert pack_response.status_code == 200, pack_response.text

    return candidate_id


async def test_generate_assessment_happy_path(
    client: AsyncClient, fake_prescreen_assessment_llm_client: FakePrescreenAssessmentLLMClient
) -> None:
    owner = await signup(client, email="owner@prescreen.com", company_name="Prescreen Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="Prescreen Candidate"
    )

    generate_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers
    )
    assert generate_response.status_code == 200, generate_response.text
    assessment = generate_response.json()

    assert assessment["fit_rating"] == "Good Fit"
    assert assessment["fit_summary"] == "A fake but deterministic fit summary for testing."
    assert assessment["strengths"] == ["Fake strength"]
    assert assessment["gaps"] == ["Fake gap"]
    assert assessment["suggested_questions"] == ["Fake suggested question"]
    assert assessment["areas_to_probe"] == ["Fake area to probe"]
    assert assessment["handoff_recommendations"] is None
    assert assessment["model_used"] == "claude-sonnet-5"

    assert len(fake_prescreen_assessment_llm_client.assessment_calls) == 1
    assert "5+ years Python" in fake_prescreen_assessment_llm_client.assessment_calls[0]

    get_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == assessment["id"]


async def test_generate_assessment_without_intelligence_pack_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@noiq.com", company_name="No IQ Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": "No Pack Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers
    )
    assert response.status_code == 404  # IntelligencePackNotFoundError


async def test_generate_assessment_without_blueprint_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@noblueprint.com", company_name="No Blueprint Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    alignment_response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["Requirement"]},
        headers=headers,
    )
    assert alignment_response.status_code == 200

    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project["id"], full_name="No Blueprint Candidate"
    )

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers
    )
    assert response.status_code == 400  # MissingHiringBlueprintError


async def test_generate_assessment_without_alignment_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@noalignment.com", company_name="No Alignment Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    patch_response = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"role_brief": "A role brief."},
        headers=headers,
    )
    assert patch_response.status_code == 200
    blueprint_response = await client.post(
        f"/api/v1/projects/{project['id']}/hiring-blueprint", headers=headers
    )
    assert blueprint_response.status_code == 200

    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "No Alignment Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    resume_bytes = _build_resume_pdf(full_name="No Alignment Candidate")
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.pdf", resume_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text

    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 200, sanitize_response.text

    # Alignment is required at intelligence-pack generation time too, so the missing
    # alignment now surfaces here rather than at the later prescreen-assessment step.
    pack_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert pack_response.status_code == 400  # MissingHiringManagerAlignmentError


async def test_handoff_recommendations_happy_path(
    client: AsyncClient, fake_prescreen_assessment_llm_client: FakePrescreenAssessmentLLMClient
) -> None:
    owner = await signup(client, email="owner@handoff.com", company_name="Handoff Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="Handoff Candidate"
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers)

    notes_response = await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={"prescreen_notes": "Candidate was strong on distributed systems."},
        headers=headers,
    )
    assert notes_response.status_code == 200

    handoff_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment/handoff", headers=headers
    )
    assert handoff_response.status_code == 200, handoff_response.text
    assert handoff_response.json()["handoff_recommendations"] == ["Fake handoff recommendation"]
    assert fake_prescreen_assessment_llm_client.handoff_calls == [
        "Candidate was strong on distributed systems."
    ]


async def test_handoff_recommendations_without_assessment_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@nohandoffassess.com", company_name="No Assess Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="No Assessment Candidate"
    )
    await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={"prescreen_notes": "Some notes."},
        headers=headers,
    )

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment/handoff", headers=headers
    )
    assert response.status_code == 404  # PrescreenAssessmentNotFoundError


async def test_handoff_recommendations_without_notes_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@nonotes.com", company_name="No Notes Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="No Notes Candidate"
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers)

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment/handoff", headers=headers
    )
    assert response.status_code == 400  # PrescreenNotesRequiredError


async def test_member_can_view_but_not_trigger_generation(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@prescreenperms.com", company_name="Prescreen Perms")
    owner_headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=owner_headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=owner_headers, project_id=project_id, full_name="Perm Test Candidate"
    )
    await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=owner_headers
    )

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@prescreenperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    generate_denied = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=member_headers
    )
    assert generate_denied.status_code == 403

    view_allowed = await client.get(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=member_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_prescreen_assessment_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsprescreen-a.com", company_name="RLS Pre A")
    headers_a = auth_headers(owner_a["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers_a)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers_a, project_id=project_id, full_name="RLS Prescreen Candidate"
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers_a)

    owner_b = await signup(client, email="owner@rlsprescreen-b.com", company_name="RLS Pre B")
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
                text("SELECT id FROM prescreen_assessments WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_prescreen_assessments() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM prescreen_assessments LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on prescreen_assessments"
    finally:
        await auth_engine.dispose()

from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender, FakeLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


def _build_resume_pdf(*, full_name: str, email: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        w=0,
        text=f"{full_name}\n{email}\nBackend engineer with Python and SQL experience.",
    )
    return bytes(pdf.output())


async def _create_project_with_alignment(client: AsyncClient, *, headers: dict) -> str:
    project = await create_project(client, headers=headers)
    alignment_response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["5+ years Python", "Distributed systems experience"]},
        headers=headers,
    )
    assert alignment_response.status_code == 200, alignment_response.text
    return project["id"]


async def _create_sanitized_candidate(
    client: AsyncClient, *, headers: dict, full_name: str, email: str, project_id: str | None = None
) -> str:
    if project_id is None:
        project_id = await _create_project_with_alignment(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": full_name, "email": email},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    resume_bytes = _build_resume_pdf(full_name=full_name, email=email)
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
    return candidate_id


async def test_generate_intelligence_pack_happy_path(
    client: AsyncClient, fake_llm_client: FakeLLMClient
) -> None:
    owner = await signup(client, email="owner@intel.com", company_name="Intel Co")
    headers = auth_headers(owner["access_token"])
    candidate_id = await _create_sanitized_candidate(
        client, headers=headers, full_name="Intel Candidate", email="intel.candidate@example.com"
    )

    generate_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert generate_response.status_code == 200, generate_response.text
    pack = generate_response.json()

    assert pack["skills"] == ["Python", "Distributed Systems"]
    assert pack["experience_summary"] == "Backend engineer with several years of experience."
    assert pack["education"] == [{"institution": "Fake University", "degree": "BSc", "field": "CS"}]
    assert pack["narrative_summary"] == "A fake but deterministic summary for testing."
    assert pack["highlights"] == ["Fake highlight matching a hiring manager requirement."]
    assert pack["industry"] == "Fintech"
    assert pack["years_experience"] == 8
    assert pack["model_used"] == "claude-sonnet-5"

    # The fake client should only ever have seen the redacted text, never the candidate's name
    # or email — proves the module never bypasses the Privacy Gateway.
    assert len(fake_llm_client.calls) == 1
    assert "Intel Candidate" not in fake_llm_client.calls[0]

    # The hiring manager's top requirements — set up by _create_project_with_alignment — must
    # reach the LLM client, since that's what "smart highlights" are compared against.
    assert fake_llm_client.requirement_calls == [
        ["5+ years Python", "Distributed systems experience"]
    ]
    assert "intel.candidate@example.com" not in fake_llm_client.calls[0]

    get_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == pack["id"]


async def test_generate_without_alignment_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@noalignment.com", company_name="No Alignment Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate_id = await _create_sanitized_candidate(
        client,
        headers=headers,
        full_name="No Alignment Candidate",
        email="no.alignment@example.com",
        project_id=project["id"],
    )

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert response.status_code == 400  # MissingHiringManagerAlignmentError


async def test_generate_without_sanitizing_first_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@nosanitize.com", company_name="No Sanitize Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Not Sanitized Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers
    )
    assert response.status_code == 404  # SanitizedProfileNotFoundError


async def test_hiring_manager_can_view_but_not_trigger_generation(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Hiring Manager has candidates.view but not candidates.update -- Recruiter (the old
    Member's successor) now has both, so it's Hiring Manager that exercises this view-only
    floor post-Phase-3."""
    owner = await signup(client, email="owner@intelperms.com", company_name="Intel Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    candidate_id = await _create_sanitized_candidate(
        client,
        headers=owner_headers,
        full_name="Perm Test Candidate",
        email="perm.intel@example.com",
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=owner_headers)

    hiring_manager = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="hiringmanager@intelperms.com",
        role="Hiring Manager",
        sent_emails=sent_emails,
    )
    hiring_manager_headers = auth_headers(hiring_manager["access_token"])

    generate_denied = await client.post(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=hiring_manager_headers
    )
    assert generate_denied.status_code == 403

    view_allowed = await client.get(
        f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=hiring_manager_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_intelligence_pack_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsintel-a.com", company_name="RLS Intel A")
    headers_a = auth_headers(owner_a["access_token"])
    candidate_id = await _create_sanitized_candidate(
        client, headers=headers_a, full_name="RLS Intel Candidate", email="rls.intel@example.com"
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/intelligence-pack", headers=headers_a)

    owner_b = await signup(client, email="owner@rlsintel-b.com", company_name="RLS Intel B")
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
                text("SELECT id FROM intelligence_packs WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_intelligence_packs() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM intelligence_packs LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on intelligence_packs"
    finally:
        await auth_engine.dispose()

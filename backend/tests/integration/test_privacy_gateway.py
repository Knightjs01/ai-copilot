from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


def _build_resume_pdf(*, full_name: str, email: str, phone: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        w=0,
        text=(
            f"{full_name}\n"
            f"{email} | {phone}\n"
            "Experienced backend engineer, 2020-2023 at Acme Corp.\n"
            "Skilled in distributed systems and API design."
        ),
    )
    return bytes(pdf.output())


async def _create_candidate_with_resume(
    client: AsyncClient, *, headers: dict, full_name: str, email: str, phone: str
) -> str:
    project = await create_project(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": full_name, "email": email},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    resume_bytes = _build_resume_pdf(full_name=full_name, email=email, phone=phone)
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.pdf", resume_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text
    return candidate_id


async def test_sanitize_redacts_pii_and_deletes_original_file(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@privacygw.com", company_name="Privacy GW Co")
    headers = auth_headers(owner["access_token"])
    candidate_id = await _create_candidate_with_resume(
        client,
        headers=headers,
        full_name="Jane Sanitize Test",
        email="jane.sanitize@example.com",
        phone="123-456-7890",
    )

    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 200, sanitize_response.text
    profile = sanitize_response.json()

    assert "Jane Sanitize Test" not in profile["redacted_text"]
    assert "jane.sanitize@example.com" not in profile["redacted_text"]
    assert "123-456-7890" not in profile["redacted_text"]
    assert "distributed systems" in profile["redacted_text"]
    assert profile["redaction_counts"]["name"] >= 1
    assert profile["redaction_counts"]["email"] == 1
    assert profile["redaction_counts"]["phone"] == 1
    assert profile["source_file_type"] == "pdf"

    # Original file must be gone — both the candidate's reference to it and the file itself.
    candidate_response = await client.get(f"/api/v1/candidates/{candidate_id}", headers=headers)
    assert candidate_response.json()["resume_original_filename"] is None

    download_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/resume", headers=headers
    )
    assert download_response.status_code == 404

    get_profile_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/sanitized-profile", headers=headers
    )
    assert get_profile_response.status_code == 200
    assert get_profile_response.json()["id"] == profile["id"]


async def test_sanitize_without_a_resume_uploaded_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@noresume.com", company_name="No Resume Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "No Resume Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers)
    assert response.status_code == 404  # ResumeNotFoundError — nothing to sanitize


async def test_sanitize_rejects_legacy_doc_format(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@legacydoc.com", company_name="Legacy Doc Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Legacy Doc Candidate"},
        headers=headers,
    )
    candidate_id = create_response.json()["id"]

    # Phase 3 upload validation accepts .doc (content-type + size only) — Phase 4 extraction is
    # what actually rejects it, since there's no reliable pure-Python .doc text extractor.
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.doc", b"not really a doc file", "application/msword")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text

    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 400


async def test_hiring_manager_can_view_but_not_trigger_sanitize(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Hiring Manager has candidates.view but not candidates.update -- Recruiter (the old
    Member's successor) now has both, so it's Hiring Manager that exercises this view-only
    floor post-Phase-3."""
    owner = await signup(client, email="owner@gwperms.com", company_name="GW Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    candidate_id = await _create_candidate_with_resume(
        client,
        headers=owner_headers,
        full_name="Perm Test Candidate",
        email="perm.test@example.com",
        phone="123-456-7890",
    )

    hiring_manager = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="hiringmanager@gwperms.com",
        role="Hiring Manager",
        sent_emails=sent_emails,
    )
    hiring_manager_headers = auth_headers(hiring_manager["access_token"])

    sanitize_denied = await client.post(
        f"/api/v1/candidates/{candidate_id}/sanitize", headers=hiring_manager_headers
    )
    assert sanitize_denied.status_code == 403

    await client.post(f"/api/v1/candidates/{candidate_id}/sanitize", headers=owner_headers)

    view_allowed = await client.get(
        f"/api/v1/candidates/{candidate_id}/sanitized-profile", headers=hiring_manager_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_sanitized_profile_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsgw-a.com", company_name="RLS GW A")
    headers_a = auth_headers(owner_a["access_token"])
    candidate_id = await _create_candidate_with_resume(
        client,
        headers=headers_a,
        full_name="RLS Test Candidate",
        email="rls.test@example.com",
        phone="123-456-7890",
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/sanitize", headers=headers_a)

    owner_b = await signup(client, email="owner@rlsgw-b.com", company_name="RLS GW B")
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
                text("SELECT id FROM sanitized_profiles WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_sanitized_profiles() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM sanitized_profiles LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on sanitized_profiles"
    finally:
        await auth_engine.dispose()

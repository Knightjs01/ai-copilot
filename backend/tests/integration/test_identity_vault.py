import uuid as uuid_module

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.modules.auth import security
from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    create_project,
    invite_and_accept,
    signup,
    step_up_headers,
)


async def _create_candidate(
    client: AsyncClient, *, headers: dict, project_id: str, full_name: str, **extra: object
) -> dict:
    response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": full_name, **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_creating_candidate_creates_exactly_one_vault_row(client: AsyncClient) -> None:
    from app.db.base import engine

    owner = await signup(client, email="owner@vaultcreate.com", company_name="Vault Create Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers)

    candidate = await _create_candidate(
        client,
        headers=headers,
        project_id=project["id"],
        full_name="Vault Test Candidate",
        email="vault.test@example.com",
    )

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            result = await conn.execute(
                text(
                    "SELECT full_name_encrypted, email_encrypted FROM candidate_identity_vaults "
                    "WHERE candidate_id = :id"
                ),
                {"id": candidate["id"]},
            )
            rows = result.fetchall()
            assert len(rows) == 1
            full_name_encrypted, email_encrypted = rows[0]
            assert security.decrypt_secret(full_name_encrypted) == "Vault Test Candidate"
            assert security.decrypt_secret(email_encrypted) == "vault.test@example.com"


async def test_candidate_responses_never_expose_pii(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@nopii.com", company_name="No PII Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    create_response = await client.post(
        "/api/v1/candidates",
        json={
            "project_id": project["id"],
            "full_name": "Hidden Candidate",
            "email": "hidden@example.com",
            "phone": "123-456-7890",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    candidate_id = create_response.json()["id"]

    _PII_KEYS = {
        "full_name",
        "email",
        "phone",
        "location",
        "current_employer",
        "current_title",
    }
    assert _PII_KEYS.isdisjoint(create_response.json().keys())

    get_response = await client.get(f"/api/v1/candidates/{candidate_id}", headers=headers)
    assert _PII_KEYS.isdisjoint(get_response.json().keys())

    list_response = await client.get(
        "/api/v1/candidates", params={"project_id": project["id"]}, headers=headers
    )
    for c in list_response.json():
        assert _PII_KEYS.isdisjoint(c.keys())


async def test_reveal_identity_requires_owner_role(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@revealperms.com", company_name="Reveal Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers)
    candidate = await _create_candidate(
        client, headers=owner_headers, project_id=project["id"], full_name="Reveal Candidate"
    )

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@revealperms.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])
    member_denied = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Hiring Manager Interview"},
        headers=member_headers,
    )
    assert member_denied.status_code == 403

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@revealperms.com",
        role="Admin",
        sent_emails=sent_emails,
    )
    admin_headers = auth_headers(admin["access_token"])
    admin_denied = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Hiring Manager Interview"},
        headers=admin_headers,
    )
    assert admin_denied.status_code == 403

    owner_allowed = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Hiring Manager Interview"},
        headers=await step_up_headers(client, headers=owner_headers),
    )
    assert owner_allowed.status_code == 200, owner_allowed.text


async def test_reveal_identity_returns_snapshot_and_records_audit_trail(
    client: AsyncClient,
) -> None:
    from app.db.base import engine

    owner = await signup(client, email="owner@revealaudit.com", company_name="Reveal Audit Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate = await _create_candidate(
        client,
        headers=headers,
        project_id=project["id"],
        full_name="Audited Candidate",
        email="audited@example.com",
    )

    reveal_response = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Background Checks"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 200, reveal_response.text
    snapshot = reveal_response.json()
    assert snapshot["full_name"] == "Audited Candidate"
    assert snapshot["email"] == "audited@example.com"
    assert snapshot["callsign"] == candidate["callsign"]
    assert snapshot["candidate_ref"] == candidate["candidate_ref"]
    assert snapshot["original_cv_status"] == "Not retained"
    event_id = snapshot["reveal_event_id"]

    close_response = await client.post(
        f"/api/v1/identity-vault/reveal-events/{event_id}/close",
        json={"duration_seconds": 42},
        headers=headers,
    )
    assert close_response.status_code == 204

    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            reveal_row = await conn.execute(
                text(
                    "SELECT reason, duration_seconds, closed_at FROM identity_reveal_events "
                    "WHERE id = :id"
                ),
                {"id": event_id},
            )
            row = reveal_row.fetchone()
            assert row is not None
            assert row[0] == "Background Checks"
            assert row[1] == 42
            assert row[2] is not None

            # Same transaction — SET LOCAL is transaction-scoped, and audit_logs is now RLS-backed
            # too (Security: close RLS coverage gap), so this needs the company context just like
            # the reveal_events query above.
            audit_row = await conn.execute(
                text(
                    "SELECT metadata FROM audit_logs "
                    "WHERE action = 'candidate.identity_revealed' AND target_id = :id"
                ),
                {"id": candidate["id"]},
            )
            audit = audit_row.fetchone()
            assert audit is not None
            assert audit[0]["reason"] == "Background Checks"


async def test_callsigns_unique_per_project_but_may_collide_across_projects(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@callsignscope.com", company_name="Callsign Co")
    headers = auth_headers(owner["access_token"])
    project_a = await create_project(client, headers=headers, title="Project A")
    project_b = await create_project(client, headers=headers, title="Project B")

    a1 = await _create_candidate(
        client, headers=headers, project_id=project_a["id"], full_name="A One"
    )
    a2 = await _create_candidate(
        client, headers=headers, project_id=project_a["id"], full_name="A Two"
    )
    assert a1["callsign"] != a2["callsign"]

    # Cross-project collisions are allowed by design — the uniqueness constraint is
    # (project_id, callsign), not a bare unique index on callsign.
    b1 = await _create_candidate(
        client, headers=headers, project_id=project_b["id"], full_name="B One"
    )
    assert b1["candidate_ref"] != a1["candidate_ref"]


async def test_candidate_ref_is_globally_unique_across_companies(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@refcompanya.com", company_name="Ref Company A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a)
    candidate_a = await _create_candidate(
        client, headers=headers_a, project_id=project_a["id"], full_name="Ref Candidate A"
    )

    owner_b = await signup(client, email="owner@refcompanyb.com", company_name="Ref Company B")
    headers_b = auth_headers(owner_b["access_token"])
    project_b = await create_project(client, headers=headers_b)
    candidate_b = await _create_candidate(
        client, headers=headers_b, project_id=project_b["id"], full_name="Ref Candidate B"
    )

    assert candidate_a["candidate_ref"] != candidate_b["candidate_ref"]


async def test_identity_vault_reveal_permission_owner_only_in_me_response(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@vaultmeperm.com", company_name="Vault Me Perm Co")
    owner_headers = auth_headers(owner["access_token"])

    owner_me = await client.get("/api/v1/auth/me", headers=owner_headers)
    assert "identity_vault.reveal" in owner_me.json()["permissions"]

    admin = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="admin@vaultmeperm.com",
        role="Admin",
        sent_emails=sent_emails,
    )
    admin_me = await client.get("/api/v1/auth/me", headers=auth_headers(admin["access_token"]))
    assert "identity_vault.reveal" not in admin_me.json()["permissions"]

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@vaultmeperm.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_me = await client.get("/api/v1/auth/me", headers=auth_headers(member["access_token"]))
    assert "identity_vault.reveal" not in member_me.json()["permissions"]


async def test_vault_field_update_not_overwritten_by_later_sanitize(client: AsyncClient) -> None:
    from fpdf import FPDF

    owner = await signup(client, email="owner@vaultnooverwrite.com", company_name="No Overwrite Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate = await _create_candidate(
        client, headers=headers, project_id=project["id"], full_name="Manual Employer Candidate"
    )

    patch_response = await client.patch(
        f"/api/v1/identity-vault/candidates/{candidate['id']}",
        json={"current_employer": "Manually Entered Corp"},
        headers=headers,
    )
    assert patch_response.status_code == 200, patch_response.text

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        w=0,
        text="Manual Employer Candidate\nmanual.employer@example.com\nBackend engineer.",
    )
    resume_bytes = bytes(pdf.output())

    await client.post(
        f"/api/v1/candidates/{candidate['id']}/resume",
        files={"file": ("resume.pdf", resume_bytes, "application/pdf")},
        headers=headers,
    )
    sanitize_response = await client.post(
        f"/api/v1/candidates/{candidate['id']}/sanitize", headers=headers
    )
    assert sanitize_response.status_code == 200, sanitize_response.text

    reveal_response = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Other"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 200, reveal_response.text
    assert reveal_response.json()["current_employer"] == "Manually Entered Corp"
    assert reveal_response.json()["email"] == "manual.employer@example.com"


async def test_rls_blocks_cross_tenant_identity_vault_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlsvault-a.com", company_name="RLS Vault A")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a)
    await _create_candidate(
        client, headers=headers_a, project_id=project_a["id"], full_name="RLS Vault Candidate"
    )

    owner_b = await signup(client, email="owner@rlsvault-b.com", company_name="RLS Vault B")
    me_a = await client.get("/api/v1/auth/me", headers=headers_a)
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(owner_b["access_token"]))
    company_a_id = me_a.json()["company_id"]
    company_b_id = me_b.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_b_id)}'")
            )
            cross_tenant_query = await conn.execute(
                text("SELECT id FROM candidate_identity_vaults WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_app_auth_role_has_no_grants_on_identity_vault_tables() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        for table in ("candidate_identity_vaults", "identity_reveal_events"):
            async with auth_engine.connect() as conn:
                try:
                    await conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))  # noqa: S608
                    raised = False
                except DBAPIError:
                    raised = True
                assert raised, f"app_auth should not have SELECT privilege on {table}"
    finally:
        await auth_engine.dispose()

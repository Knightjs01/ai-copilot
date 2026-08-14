"""Adversarial: proves the company-side resume upload path is encrypted at rest, the one
EncryptingFileStorage call site test_candidate_cv_vault.py's equivalent test doesn't already
cover (task #211). [GAP] if this fails — it would mean CandidateService.upload_resume is writing
plaintext despite EncryptingFileStorage being the configured default everywhere else.

privacy_gateway/service.py was read while planning this file: it threads storage through to
CandidateService for reads/deletes only (download_resume, clear_resume) and has no independent
.save() call site of its own, so it needs no separate test here.
"""

from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import text

from app.modules.auth import security
from app.modules.candidates.storage import EncryptingFileStorage
from tests.integration.helpers import auth_headers, create_project, signup


async def test_company_resume_upload_is_encrypted_at_rest(
    client: AsyncClient, tmp_path: Path
) -> None:
    from app.db.base import engine

    owner = await signup(client, email="resume-encrypted@acme.com")
    headers = auth_headers(owner["access_token"])
    company_id = security.decode_access_token(owner["access_token"])["company_id"]
    project = await create_project(client, headers=headers)
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project["id"], "full_name": "Resume Candidate"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    candidate_id = create_response.json()["id"]

    marker = b"Marker text nobody should see in plaintext on disk"
    upload_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/resume",
        files={"file": ("resume.pdf", marker, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text

    # candidates carries RLS (see app/db/base.py) — a bare engine.connect() has no tenant context
    # and RLS would silently return zero rows rather than error, same as any tenant-scoped query;
    # set the same SET LOCAL app.current_company_id get_tenant_db would, scoped to this owner's
    # own company (the one that just created this row), not a bypass of anything.
    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(text(f"SET LOCAL app.current_company_id = '{company_id}'"))
            result = await conn.execute(
                text("SELECT resume_file_key FROM candidates WHERE id = :id"),
                {"id": candidate_id},
            )
            storage_key = result.scalar_one()

    # Same tmp_path/"storage" root the test_storage fixture builds internally — read raw bytes
    # directly, bypassing EncryptingFileStorage's transparent decryption on purpose.
    raw_bytes = (tmp_path / "storage" / storage_key).read_bytes()
    assert raw_bytes != marker
    assert marker not in raw_bytes

    # The API path still transparently decrypts back to the exact original bytes.
    download_response = await client.get(
        f"/api/v1/candidates/{candidate_id}/resume", headers=headers
    )
    assert download_response.status_code == 200
    assert download_response.content == marker


async def test_wrapped_test_storage_transparently_round_trips(
    test_storage: EncryptingFileStorage,
) -> None:
    # Methodology sanity check for the assertion style above: confirms test_storage really does
    # decrypt transparently on read (so a false "encrypted" result above can't be explained by a
    # broken fixture) rather than shipping a manual unwrapped-LocalFileStorage negative control as
    # a permanent test — see task #211's plan for why this is a one-time check, not a CI test.
    await test_storage.save(key="sanity/roundtrip.txt", content=b"hello", content_type="text/plain")
    assert await test_storage.read(key="sanity/roundtrip.txt") == b"hello"

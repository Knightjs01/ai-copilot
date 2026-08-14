from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text

from app.modules.candidates.storage import LocalFileStorage
from tests.conftest import FakePassportLLMClient
from tests.integration.helpers import auth_headers, candidate_signup, signup


def _build_cv_pdf(text_body: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(w=0, text=text_body)
    return bytes(pdf.output())


async def _parse_cv(
    client: AsyncClient, *, headers: dict, filename: str = "cv.pdf", text_body: str = "My CV"
) -> tuple[dict, bytes]:
    # Returns the exact bytes uploaded (not just the parsed JSON) — a test asserting the
    # downloaded original matches what was uploaded must compare against this, not a freshly
    # regenerated PDF: fpdf2 embeds a creation timestamp, so two calls with identical text can
    # still produce different bytes.
    cv_bytes = _build_cv_pdf(text_body)
    response = await client.post(
        "/api/v1/phantom-passport/parse-cv",
        files={"file": (filename, cv_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json(), cv_bytes


async def _save_passport(
    client: AsyncClient, *, headers: dict, headline: str = "Staff Engineer"
) -> dict:
    payload = {
        "headline": headline,
        "personal_info": {"legal_name": "Jamie Candidate"},
        "career_entries": [
            {
                "title": "VP Product",
                "company_name": "Stripe",
                "company_name_anonymized": "Global Payments Platform",
                "is_current": True,
            }
        ],
    }
    response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _approve(client: AsyncClient, *, headers: dict) -> dict:
    response = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def test_versions_list_is_empty_not_404_before_any_passport_exists(
    client: AsyncClient,
) -> None:
    tokens = await candidate_signup(client, email="noversions@example.com")
    headers = auth_headers(tokens["access_token"])
    response = await client.get("/api/v1/phantom-passport/versions", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_original_cv_absent_before_upload(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="novault@example.com")
    headers = auth_headers(tokens["access_token"])
    response = await client.get("/api/v1/phantom-passport/original-cv", headers=headers)
    assert response.status_code == 404


async def test_parse_cv_persists_and_can_be_downloaded(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="vault@example.com")
    headers = auth_headers(tokens["access_token"])
    _result, uploaded_bytes = await _parse_cv(
        client, headers=headers, filename="my-cv.pdf", text_body="Original CV text"
    )

    status_response = await client.get("/api/v1/phantom-passport/original-cv", headers=headers)
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["original_filename"] == "my-cv.pdf"

    download_response = await client.get(
        "/api/v1/phantom-passport/original-cv/download", headers=headers
    )
    assert download_response.status_code == 200, download_response.text
    assert download_response.content == uploaded_bytes


async def test_replacing_cv_deletes_old_storage_file(
    client: AsyncClient,
    fake_passport_llm_client: FakePassportLLMClient,
    test_storage: LocalFileStorage,
) -> None:
    from app.db.base import engine

    tokens = await candidate_signup(client, email="replace-vault@example.com")
    headers = auth_headers(tokens["access_token"])
    await _parse_cv(client, headers=headers, filename="first.pdf", text_body="First version")

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT storage_key FROM candidate_cv_documents"))
        old_key = result.scalar_one()

    _result, second_bytes = await _parse_cv(
        client, headers=headers, filename="second.pdf", text_body="Second version"
    )

    download_response = await client.get(
        "/api/v1/phantom-passport/original-cv/download", headers=headers
    )
    assert download_response.content == second_bytes

    try:
        await test_storage.read(key=old_key)
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised, "replaced CV file should have been deleted from storage"


async def test_delete_original_cv(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="delete-vault@example.com")
    headers = auth_headers(tokens["access_token"])
    await _parse_cv(client, headers=headers)

    delete_response = await client.delete("/api/v1/phantom-passport/original-cv", headers=headers)
    assert delete_response.status_code == 204

    status_response = await client.get("/api/v1/phantom-passport/original-cv", headers=headers)
    assert status_response.status_code == 404


async def test_candidate_cv_vaults_are_isolated(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens_a = await candidate_signup(client, email="vault-a@example.com")
    tokens_b = await candidate_signup(client, email="vault-b@example.com")
    headers_a = auth_headers(tokens_a["access_token"])
    headers_b = auth_headers(tokens_b["access_token"])

    await _parse_cv(client, headers=headers_a, filename="candidate-a.pdf")

    status_b = await client.get("/api/v1/phantom-passport/original-cv", headers=headers_b)
    assert status_b.status_code == 404

    delete_b = await client.delete("/api/v1/phantom-passport/original-cv", headers=headers_b)
    assert delete_b.status_code == 404

    status_a = await client.get("/api/v1/phantom-passport/original-cv", headers=headers_a)
    assert status_a.status_code == 200
    assert status_a.json()["original_filename"] == "candidate-a.pdf"


async def test_apply_requires_approved_passport(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@vault-gate.com")
    owner_headers = auth_headers(owner["access_token"])
    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own the platform.",
            "description": "Full description.",
        },
        headers=owner_headers,
    )
    job = job_response.json()
    await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=owner_headers)

    tokens = await candidate_signup(client, email="unapproved@vault-gate.com")
    headers = auth_headers(tokens["access_token"])
    await _save_passport(client, headers=headers)

    denied = await client.post(f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=headers)
    assert denied.status_code == 400

    await _approve(client, headers=headers)

    allowed = await client.post(f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=headers)
    assert allowed.status_code == 201, allowed.text


async def test_approve_creates_incrementing_versions(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="versions@example.com")
    headers = auth_headers(tokens["access_token"])
    await _save_passport(client, headers=headers, headline="First headline")

    first_version = await _approve(client, headers=headers)
    assert first_version["version_number"] == 1

    passport = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert passport.json()["current_version_number"] == 1

    await _save_passport(client, headers=headers, headline="Second headline")
    second_version = await _approve(client, headers=headers)
    assert second_version["version_number"] == 2

    versions_response = await client.get("/api/v1/phantom-passport/versions", headers=headers)
    assert versions_response.status_code == 200, versions_response.text
    version_numbers = [v["version_number"] for v in versions_response.json()]
    assert version_numbers == [2, 1]


async def test_editing_after_approval_does_not_change_an_already_submitted_application(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@vault-freeze.com")
    owner_headers = auth_headers(owner["access_token"])
    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own the platform.",
            "description": "Full description.",
        },
        headers=owner_headers,
    )
    job = job_response.json()
    await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=owner_headers)

    tokens = await candidate_signup(client, email="applicant@vault-freeze.com")
    candidate_headers = auth_headers(tokens["access_token"])
    await _save_passport(client, headers=candidate_headers, headline="Version 1 headline")
    await _approve(client, headers=candidate_headers)

    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text

    # Edit and re-approve — the candidate now has a "Version 2" they'd use for future
    # applications, but the application submitted above must stay frozen to what was true when
    # it was submitted.
    await _save_passport(client, headers=candidate_headers, headline="Version 2 headline")
    await _approve(client, headers=candidate_headers)

    applicants_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert applicants_response.status_code == 200, applicants_response.text
    applicants = applicants_response.json()
    assert len(applicants) == 1
    assert applicants[0]["headline"] == "Version 1 headline"
    raw_body = applicants_response.text
    assert "Version 2 headline" not in raw_body


async def test_new_application_after_reapproval_reflects_the_new_version(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@vault-freeze-new.com")
    owner_headers = auth_headers(owner["access_token"])

    async def _create_and_publish(title: str) -> dict:
        response = await client.post(
            "/api/v1/shadow-jobs",
            json={"title": title, "summary": "Summary.", "description": "Description."},
            headers=owner_headers,
        )
        job = response.json()
        await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=owner_headers)
        return job

    job_one = await _create_and_publish("Role One")
    job_two = await _create_and_publish("Role Two")

    tokens = await candidate_signup(client, email="applicant@vault-freeze-new.com")
    candidate_headers = auth_headers(tokens["access_token"])
    await _save_passport(client, headers=candidate_headers, headline="Version 1 headline")
    await _approve(client, headers=candidate_headers)
    await client.post(f"/api/v1/shadow-jobs/board/{job_one['id']}/apply", headers=candidate_headers)

    await _save_passport(client, headers=candidate_headers, headline="Version 2 headline")
    await _approve(client, headers=candidate_headers)
    second_apply = await client.post(
        f"/api/v1/shadow-jobs/board/{job_two['id']}/apply", headers=candidate_headers
    )
    assert second_apply.status_code == 201, second_apply.text

    applicants_one = await client.get(
        f"/api/v1/shadow-jobs/mine/{job_one['id']}/applicants", headers=owner_headers
    )
    assert applicants_one.json()[0]["headline"] == "Version 1 headline"

    applicants_two = await client.get(
        f"/api/v1/shadow-jobs/mine/{job_two['id']}/applicants", headers=owner_headers
    )
    assert applicants_two.json()[0]["headline"] == "Version 2 headline"


async def test_deleting_original_cv_does_not_break_an_approved_version(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="delete-after-approve@example.com")
    headers = auth_headers(tokens["access_token"])
    await _parse_cv(client, headers=headers, filename="source.pdf")
    await _save_passport(client, headers=headers)
    version = await _approve(client, headers=headers)
    assert version["source_cv_filename"] == "source.pdf"

    delete_response = await client.delete("/api/v1/phantom-passport/original-cv", headers=headers)
    assert delete_response.status_code == 204

    versions_response = await client.get("/api/v1/phantom-passport/versions", headers=headers)
    assert versions_response.status_code == 200, versions_response.text
    # The historical record survives — filename was captured by value at approval time, not
    # joined live through the (now-deleted) original document row.
    assert versions_response.json()[0]["source_cv_filename"] == "source.pdf"

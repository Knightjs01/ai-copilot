from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import text

from tests.conftest import FakePassportLLMClient
from tests.integration.helpers import auth_headers, candidate_signup


def _build_cv_pdf(*, full_name: str, email: str, phone: str, company: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        w=0,
        text=(
            f"{full_name}\n{email} | {phone}\n\n"
            f"VP Product\n{company}\n2021-Present\n"
            "Led product strategy for the platform. Scaled team from 12 to 40."
        ),
    )
    return bytes(pdf.output())


async def _default_passport_payload() -> dict:
    return {
        "headline": "Senior Product Leader",
        "seniority": "Senior",
        "years_experience": 12,
        "summary": "A senior product leader with FinTech experience.",
        "skills": ["Product Strategy", "Team Leadership"],
        "industries": ["FinTech", "B2B SaaS"],
        "location": "London, UK",
        "remote_preference": "hybrid",
        "salary_min": 140000,
        "salary_max": 170000,
        "notice_period": "one_month",
        "career_intent": "open_to_opportunity",
        "personal_info": {
            "legal_name": "Jamie Candidate",
            "phone": "+44 20 7946 0958",
            "address": "1 Example Street, London",
        },
        "career_entries": [
            {
                "title": "VP Product",
                "company_name": "Stripe",
                "company_name_anonymized": "Global Payments Platform",
                "start_date": "2021-01-01",
                "is_current": True,
                "responsibilities": "Led product strategy.",
                "achievements": ["Scaled team from 12 to 40"],
            }
        ],
    }


async def test_get_passport_before_creation_is_404(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="nopassport@example.com")
    response = await client.get(
        "/api/v1/phantom-passport/me", headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 404


async def test_save_and_read_back_passport(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="save@example.com", full_name="Jamie Candidate")
    headers = auth_headers(tokens["access_token"])
    payload = await _default_passport_payload()

    save_response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert save_response.status_code == 200, save_response.text
    body = save_response.json()

    assert body["headline"] == "Senior Product Leader"
    assert body["career_intent"] == "open_to_opportunity"
    assert body["verification_status"] == "unverified"
    assert body["personal_info"]["legal_name"] == "Jamie Candidate"
    assert body["personal_info"]["phone"] == "+44 20 7946 0958"
    assert len(body["career_entries"]) == 1
    entry = body["career_entries"][0]
    assert entry["company_name"] == "Stripe"
    assert entry["company_name_anonymized"] == "Global Payments Platform"
    assert entry["achievements"] == ["Scaled team from 12 to 40"]

    get_response = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == body


async def test_completion_percentage_reflects_filled_fields(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="completion@example.com")
    headers = auth_headers(tokens["access_token"])

    minimal_payload = {
        "personal_info": {"legal_name": "Minimal Candidate"},
        "career_entries": [],
    }
    minimal_response = await client.put(
        "/api/v1/phantom-passport/me", json=minimal_payload, headers=headers
    )
    assert minimal_response.status_code == 200, minimal_response.text
    assert minimal_response.json()["completion_percentage"] == 0

    full_payload = await _default_passport_payload()
    full_payload["personal_info"]["legal_name"] = "Minimal Candidate"
    full_response = await client.put(
        "/api/v1/phantom-passport/me", json=full_payload, headers=headers
    )
    assert full_response.status_code == 200, full_response.text
    assert full_response.json()["completion_percentage"] == 100


async def test_personal_data_is_encrypted_at_rest(client: AsyncClient) -> None:
    from app.db.base import engine

    tokens = await candidate_signup(
        client, email="encrypted@example.com", full_name="Secret Identity"
    )
    headers = auth_headers(tokens["access_token"])
    payload = await _default_passport_payload()
    payload["personal_info"]["legal_name"] = "Secret Identity"
    save_response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert save_response.status_code == 200, save_response.text

    # No RLS on these tables (see migration 0016) — the plain app_runtime connection can read
    # them directly, but the raw plaintext must never appear in the stored ciphertext column.
    async with engine.connect() as conn:
        personal_info_row = await conn.execute(
            text("SELECT legal_name_encrypted, phone_encrypted FROM passport_personal_info")
        )
        legal_name_encrypted, phone_encrypted = personal_info_row.fetchone()
        assert "Secret Identity" not in legal_name_encrypted
        assert "+44 20 7946 0958" not in phone_encrypted

        career_row = await conn.execute(
            text(
                "SELECT company_name_encrypted, company_name_anonymized FROM passport_career_entries"
            )
        )
        company_name_encrypted, company_name_anonymized = career_row.fetchone()
        assert "Stripe" not in company_name_encrypted
        assert company_name_anonymized == "Global Payments Platform"


async def test_parse_cv_returns_structured_preview_without_persisting(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="parse@example.com", full_name="Jamie Analyst")
    headers = auth_headers(tokens["access_token"])

    cv_bytes = _build_cv_pdf(
        full_name="Jamie Analyst",
        email="jamie.analyst@example.com",
        phone="123-456-7890",
        company="Stripe",
    )
    response = await client.post(
        "/api/v1/phantom-passport/parse-cv",
        files={"file": ("cv.pdf", cv_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["headline"] == "Senior Product Leader"
    assert body["career_entries"][0]["company_name"] == "Stripe"
    assert body["career_entries"][0]["company_name_anonymized"] == "Global Payments Platform"
    assert body["detected_phone"] is not None

    # Nothing was persisted — parse-cv is a preview only.
    get_response = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert get_response.status_code == 404


async def test_parse_cv_never_sends_candidate_name_or_email_to_the_llm(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(
        client, email="privacy-check@example.com", full_name="Jamie Analyst"
    )
    headers = auth_headers(tokens["access_token"])

    cv_bytes = _build_cv_pdf(
        full_name="Jamie Analyst",
        email="jamie.analyst@example.com",
        phone="123-456-7890",
        company="Stripe",
    )
    response = await client.post(
        "/api/v1/phantom-passport/parse-cv",
        files={"file": ("cv.pdf", cv_bytes, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    assert len(fake_passport_llm_client.calls) == 1
    redacted_text_sent_to_llm = fake_passport_llm_client.calls[0]
    assert "Jamie" not in redacted_text_sent_to_llm
    assert "Analyst" not in redacted_text_sent_to_llm


async def test_callsign_is_null_until_first_approval(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="callsign@example.com")
    headers = auth_headers(tokens["access_token"])
    payload = await _default_passport_payload()

    save_response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert save_response.status_code == 200, save_response.text
    assert save_response.json()["callsign"] is None

    approve_response = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert approve_response.status_code == 200, approve_response.text

    get_response = await client.get("/api/v1/phantom-passport/me", headers=headers)
    assert get_response.status_code == 200, get_response.text
    callsign = get_response.json()["callsign"]
    assert callsign is not None
    assert "-" in callsign


async def test_callsign_is_stable_across_reapproval(client: AsyncClient) -> None:
    tokens = await candidate_signup(client, email="callsign-stable@example.com")
    headers = auth_headers(tokens["access_token"])
    payload = await _default_passport_payload()
    await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)

    first_approve = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert first_approve.status_code == 200, first_approve.text
    first_callsign = (await client.get("/api/v1/phantom-passport/me", headers=headers)).json()[
        "callsign"
    ]

    # Edit and re-approve — the Callsign must not be regenerated on a second approval.
    payload["headline"] = "Updated Headline"
    await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    second_approve = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert second_approve.status_code == 200, second_approve.text
    second_callsign = (await client.get("/api/v1/phantom-passport/me", headers=headers)).json()[
        "callsign"
    ]

    assert first_callsign == second_callsign


async def test_suggest_summary_happy_path(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="suggest-summary@example.com")
    headers = auth_headers(tokens["access_token"])

    response = await client.post(
        "/api/v1/phantom-passport/suggest-summary",
        json={
            "headline": "Senior Product Leader",
            "summary": "Led things.",
            "skills": ["Product Strategy"],
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "suggested_summary": "A fake but deterministic improved summary for testing."
    }
    assert fake_passport_llm_client.summary_suggestion_calls == ["Led things."]


async def test_suggest_skills_happy_path(
    client: AsyncClient, fake_passport_llm_client: FakePassportLLMClient
) -> None:
    tokens = await candidate_signup(client, email="suggest-skills@example.com")
    headers = auth_headers(tokens["access_token"])

    response = await client.post(
        "/api/v1/phantom-passport/suggest-skills",
        json={
            "headline": "Senior Product Leader",
            "summary": "Led a payments platform.",
            "existing_skills": ["Leadership"],
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"suggested_skills": ["Fake suggested skill"]}
    assert fake_passport_llm_client.skills_suggestion_calls == [["Leadership"]]

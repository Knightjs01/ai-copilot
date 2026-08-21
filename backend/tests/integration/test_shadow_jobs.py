from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, invite_and_accept, signup

_JOB_PAYLOAD = {
    "title": "Staff Product Designer",
    "department": "Design",
    "seniority": "Staff",
    "employment_type": "full_time",
    "location": "Remote",
    "remote_preference": "remote",
    "salary_min": 120000,
    "salary_max": 150000,
    "summary": "Own product design for our core platform.",
    "description": "A full description of the role and its responsibilities.",
    "requirements": ["8+ years of product design experience"],
}


async def _create_job(client: AsyncClient, *, headers: dict, payload: dict = _JOB_PAYLOAD) -> dict:
    response = await client.post("/api/v1/shadow-jobs", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def _publish_job(client: AsyncClient, *, headers: dict, job_id: str) -> dict:
    response = await client.post(f"/api/v1/shadow-jobs/mine/{job_id}/publish", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _save_passport(client: AsyncClient, *, headers: dict) -> None:
    payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader with FinTech experience.",
        "skills": ["Product Strategy"],
        "industries": ["FinTech"],
        "career_intent": "actively_looking",
        "personal_info": {"legal_name": "Jamie Candidate", "phone": "+44 20 7946 0958"},
        "career_entries": [
            {
                "title": "VP Product",
                "company_name": "Stripe",
                "company_name_anonymized": "Global Payments Platform",
                "start_date": "2021-01-01",
                "is_current": True,
                "achievements": ["Scaled team from 12 to 40"],
            }
        ],
    }
    response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert response.status_code == 200, response.text

    # Applying now requires an approved Passport — see phantom_passport's Candidate Vault /
    # approval gate work. Approve it here so every existing apply-flow test keeps exercising the
    # same "apply with whatever the Passport holds" behavior as before.
    approve_response = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert approve_response.status_code == 200, approve_response.text


async def test_owner_can_create_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-perm.com")
    job = await _create_job(client, headers=auth_headers(owner["access_token"]))
    assert job["status"] == "draft"
    assert job["title"] == _JOB_PAYLOAD["title"]
    assert job["applicant_count"] == 0


async def test_recruiter_can_create_and_publish_job(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Recruiter (renamed + permission-expanded from the old Member) now has shadow_jobs.create
    and shadow_jobs.update -- unlike old Member, which was view-only for Shadow jobs."""
    owner = await signup(client, email="owner@shadowjobs-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=owner_headers)

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@shadowjobs-memberperm.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])

    create_allowed = await client.post(
        "/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=recruiter_headers
    )
    assert create_allowed.status_code == 201, create_allowed.text

    publish_allowed = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=recruiter_headers
    )
    assert publish_allowed.status_code == 200, publish_allowed.text

    view_response = await client.get("/api/v1/shadow-jobs/mine", headers=recruiter_headers)
    assert view_response.status_code == 200, view_response.text


async def test_publish_and_close_job_lifecycle(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-lifecycle.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)

    published = await _publish_job(client, headers=headers, job_id=job["id"])
    assert published["status"] == "published"
    assert published["published_at"] is not None

    closed_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/close", headers=headers
    )
    assert closed_response.status_code == 200, closed_response.text
    assert closed_response.json()["status"] == "closed"


async def test_public_board_only_shows_published_jobs_across_companies(
    client: AsyncClient,
) -> None:
    owner_a = await signup(client, email="owner@shadowjobs-board-a.com", company_name="Company A")
    owner_b = await signup(client, email="owner@shadowjobs-board-b.com", company_name="Company B")
    headers_a = auth_headers(owner_a["access_token"])
    headers_b = auth_headers(owner_b["access_token"])

    published_job = await _create_job(client, headers=headers_a)
    await _publish_job(client, headers=headers_a, job_id=published_job["id"])
    draft_job = await _create_job(
        client, headers=headers_b, payload={**_JOB_PAYLOAD, "title": "Unpublished Role"}
    )

    board_response = await client.get("/api/v1/shadow-jobs/board")
    assert board_response.status_code == 200, board_response.text
    board = board_response.json()
    board_ids = {job["id"] for job in board}

    assert published_job["id"] in board_ids
    assert draft_job["id"] not in board_ids

    listed = next(job for job in board if job["id"] == published_job["id"])
    assert listed["company_name"] == "Company A"

    detail_response = await client.get(f"/api/v1/shadow-jobs/board/{published_job['id']}")
    assert detail_response.status_code == 200, detail_response.text

    unpublished_detail = await client.get(f"/api/v1/shadow-jobs/board/{draft_job['id']}")
    assert unpublished_detail.status_code == 404


async def test_apply_requires_published_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-apply-unpublished.com")
    job = await _create_job(client, headers=auth_headers(owner["access_token"]))

    candidate_tokens = await candidate_signup(client, email="applicant@shadowjobs-unpub.com")
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)

    response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert response.status_code == 400


async def test_apply_requires_a_passport(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-apply-nopassport.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(client, email="nopassport@shadowjobs-apply.com")
    response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply",
        headers=auth_headers(candidate_tokens["access_token"]),
    )
    assert response.status_code == 400


async def test_apply_success_generates_callsign(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-apply-success.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(client, email="applicant@shadowjobs-success.com")
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)

    response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "submitted"
    assert body["job_title"] == _JOB_PAYLOAD["title"]
    assert "-" in body["callsign"]

    my_applications = await client.get(
        "/api/v1/shadow-jobs/applications/me", headers=candidate_headers
    )
    assert my_applications.status_code == 200, my_applications.text
    assert len(my_applications.json()) == 1
    assert my_applications.json()[0]["callsign"] == body["callsign"]


async def test_duplicate_application_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-dup.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(client, email="applicant@shadowjobs-dup.com")
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)

    first = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert second.status_code == 409


async def test_company_applicant_list_is_anonymized(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-anon.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(
        client, email="applicant@shadowjobs-anon.com", full_name="Secret Applicant"
    )
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    callsign = apply_response.json()["callsign"]

    applicants_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert applicants_response.status_code == 200, applicants_response.text
    applicants = applicants_response.json()
    assert len(applicants) == 1
    profile = applicants[0]

    assert profile["callsign"] == callsign
    assert profile["headline"] == "Senior Product Leader"
    assert profile["career_entries"][0]["company_name_anonymized"] == "Global Payments Platform"

    raw_body = applicants_response.text
    assert "Secret Applicant" not in raw_body
    assert "Stripe" not in raw_body
    assert "legal_name" not in raw_body
    assert "phone" not in raw_body
    assert "personal_info" not in raw_body

    job_with_count = await client.get(f"/api/v1/shadow-jobs/mine/{job['id']}", headers=headers)
    assert job_with_count.json()["applicant_count"] == 1


async def test_company_applicant_list_never_exposes_passport_callsign(client: AsyncClient) -> None:
    # The Passport's own persistent Callsign (generated once, at first approval — see
    # phantom_passport/service.py) is a genuinely different identity from the per-application
    # Callsign this endpoint legitimately returns (profile["callsign"] above). This confirms the
    # isolation holds: a company can never see the Passport-level Callsign anywhere.
    owner = await signup(client, email="owner@shadowjobs-passport-callsign.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(
        client, email="applicant@shadowjobs-passport-callsign.com", full_name="Jordan Applicant"
    )
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)

    passport_response = await client.get("/api/v1/phantom-passport/me", headers=candidate_headers)
    assert passport_response.status_code == 200, passport_response.text
    passport_callsign = passport_response.json()["callsign"]
    assert passport_callsign is not None

    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    application_callsign = apply_response.json()["callsign"]
    assert application_callsign != passport_callsign

    applicants_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert applicants_response.status_code == 200, applicants_response.text
    assert passport_callsign not in applicants_response.text


async def test_candidate_can_withdraw_application(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowjobs-withdraw.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_job(client, headers=headers)
    await _publish_job(client, headers=headers, job_id=job["id"])

    candidate_tokens = await candidate_signup(client, email="applicant@shadowjobs-withdraw.com")
    candidate_headers = auth_headers(candidate_tokens["access_token"])
    await _save_passport(client, headers=candidate_headers)
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    application_id = apply_response.json()["id"]

    withdraw_response = await client.post(
        f"/api/v1/shadow-jobs/applications/me/{application_id}/withdraw",
        headers=candidate_headers,
    )
    assert withdraw_response.status_code == 200, withdraw_response.text
    assert withdraw_response.json()["status"] == "withdrawn"

    # Withdrawing twice is rejected.
    second_withdraw = await client.post(
        f"/api/v1/shadow-jobs/applications/me/{application_id}/withdraw",
        headers=candidate_headers,
    )
    assert second_withdraw.status_code == 400

    # Company still sees the withdrawn application, with its status updated.
    applicants_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert applicants_response.json()[0]["status"] == "withdrawn"

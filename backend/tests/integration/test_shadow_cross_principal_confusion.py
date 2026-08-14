"""Adversarial: full endpoint matrix on the two routers that mix both principal types in one
router (shadow_jobs, shadow_reveal) — every route is individually gated correctly today, but
nothing before this file proved there's no endpoint where the wrong principal's token slips
through. All [REGRESSION]. Real job/application IDs are used throughout (not random UUIDs) so a
false pass from hitting a 404-before-auth-check code path is ruled out — the auth dependency must
reject before the route body/ID lookup ever runs.

GET /shadow-jobs/board and /shadow-jobs/board/{job_id} are deliberately excluded — they're public
by design (no auth dependency at all), not an oversight.
"""

from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, signup

_JOB_PAYLOAD = {
    "title": "Staff Product Designer",
    "summary": "Own product design for our core platform.",
    "description": "A full description of the role and its responsibilities.",
}


async def _create_and_publish_job(client: AsyncClient, *, headers: dict) -> dict:
    response = await client.post("/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=headers)
    assert response.status_code == 201, response.text
    job = response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def _apply_with_new_candidate(
    client: AsyncClient, *, job_id: str, email: str, full_name: str = "Jamie Candidate"
) -> tuple[dict, dict]:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    passport_payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader.",
        "career_intent": "actively_looking",
        "personal_info": {"legal_name": full_name, "phone": "+44 20 7946 0958"},
        "career_entries": [
            {
                "title": "VP Product",
                "company_name": "Stripe",
                "company_name_anonymized": "Global Payments Platform",
                "is_current": True,
            }
        ],
    }
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=passport_payload, headers=candidate_headers
    )
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job_id}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    return apply_response.json(), candidate_headers


async def _setup(client: AsyncClient, *, prefix: str) -> tuple[dict, dict, dict, dict]:
    """Returns (company_headers, candidate_headers, job, application) for a fully set-up
    published job with one submitted application — the shared fixture every test below needs."""

    owner = await signup(client, email=f"{prefix}-owner@acme.com")
    company_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=company_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email=f"{prefix}-applicant@example.com"
    )
    return company_headers, candidate_headers, job, application


# --- Candidate token against company-only shadow_jobs routes ----------------------------------


async def test_candidate_token_cannot_create_job(client: AsyncClient) -> None:
    _, candidate_headers, _job, _application = await _setup(client, prefix="xconf-create")
    response = await client.post(
        "/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=candidate_headers
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_list_company_jobs(client: AsyncClient) -> None:
    _, candidate_headers, _job, _application = await _setup(client, prefix="xconf-list")
    response = await client.get("/api/v1/shadow-jobs/mine", headers=candidate_headers)
    assert response.status_code == 401


async def test_candidate_token_cannot_get_company_job(client: AsyncClient) -> None:
    _, candidate_headers, job, _application = await _setup(client, prefix="xconf-get")
    response = await client.get(f"/api/v1/shadow-jobs/mine/{job['id']}", headers=candidate_headers)
    assert response.status_code == 401


async def test_candidate_token_cannot_update_job(client: AsyncClient) -> None:
    _, candidate_headers, job, _application = await _setup(client, prefix="xconf-update")
    response = await client.patch(
        f"/api/v1/shadow-jobs/mine/{job['id']}",
        json={"title": "Hijacked"},
        headers=candidate_headers,
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_publish_job(client: AsyncClient) -> None:
    _, candidate_headers, job, _application = await _setup(client, prefix="xconf-publish")
    response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=candidate_headers
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_close_job(client: AsyncClient) -> None:
    _, candidate_headers, job, _application = await _setup(client, prefix="xconf-close")
    response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/close", headers=candidate_headers
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_list_applicants(client: AsyncClient) -> None:
    _, candidate_headers, job, _application = await _setup(client, prefix="xconf-applicants")
    response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=candidate_headers
    )
    assert response.status_code == 401


# --- Company token against candidate-only shadow_jobs routes ----------------------------------


async def test_company_token_cannot_apply_to_job(client: AsyncClient) -> None:
    company_headers, _candidate_headers, job, _application = await _setup(
        client, prefix="xconf-apply"
    )
    response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=company_headers
    )
    assert response.status_code == 401


async def test_company_token_cannot_list_my_applications(client: AsyncClient) -> None:
    company_headers, _candidate_headers, _job, _application = await _setup(
        client, prefix="xconf-my-apps"
    )
    response = await client.get("/api/v1/shadow-jobs/applications/me", headers=company_headers)
    assert response.status_code == 401


async def test_company_token_cannot_get_my_application(client: AsyncClient) -> None:
    company_headers, _candidate_headers, _job, application = await _setup(
        client, prefix="xconf-my-app"
    )
    response = await client.get(
        f"/api/v1/shadow-jobs/applications/me/{application['id']}", headers=company_headers
    )
    assert response.status_code == 401


async def test_company_token_cannot_withdraw_application(client: AsyncClient) -> None:
    company_headers, _candidate_headers, _job, application = await _setup(
        client, prefix="xconf-withdraw"
    )
    response = await client.post(
        f"/api/v1/shadow-jobs/applications/me/{application['id']}/withdraw", headers=company_headers
    )
    assert response.status_code == 401


# --- Candidate token against company-only shadow_reveal routes --------------------------------


async def test_candidate_token_cannot_request_reveal(client: AsyncClient) -> None:
    _, candidate_headers, job, application = await _setup(client, prefix="xconf-reveal-request")
    response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=candidate_headers,
    )
    assert response.status_code == 401


async def test_candidate_token_cannot_get_revealed_identity(client: AsyncClient) -> None:
    company_headers, candidate_headers, job, application = await _setup(
        client, prefix="xconf-reveal-get"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=company_headers,
    )
    response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=candidate_headers,
    )
    assert response.status_code == 401


# --- Company token against candidate-only shadow_reveal routes --------------------------------


async def test_company_token_cannot_get_my_reveal_request(client: AsyncClient) -> None:
    company_headers, _candidate_headers, job, application = await _setup(
        client, prefix="xconf-my-reveal-get"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=company_headers,
    )
    response = await client.get(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}", headers=company_headers
    )
    assert response.status_code == 401


async def test_company_token_cannot_respond_to_reveal_request(client: AsyncClient) -> None:
    company_headers, _candidate_headers, job, application = await _setup(
        client, prefix="xconf-my-reveal-respond"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=company_headers,
    )
    response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=company_headers,
    )
    assert response.status_code == 401

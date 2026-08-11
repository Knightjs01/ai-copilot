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

    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job_id}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    return apply_response.json(), candidate_headers


async def test_request_reveal_transitions_application_status(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-request.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-request.com"
    )

    request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Moving to final interview"},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text
    body = request_response.json()
    assert body["status"] == "pending"
    assert body["callsign"] == application["callsign"]

    applications_response = await client.get(
        "/api/v1/shadow-jobs/applications/me", headers=_candidate_headers
    )
    assert applications_response.json()[0]["status"] == "reveal_requested"


async def test_duplicate_reveal_request_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-dup.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-dup.com"
    )

    first = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert second.status_code == 409


async def test_candidate_can_view_and_approve_reveal_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-approve.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-approve.com",
        full_name="Secret Applicant",
    )

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Ready to move forward"},
        headers=headers,
    )

    pending_view = await client.get(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}", headers=candidate_headers
    )
    assert pending_view.status_code == 200, pending_view.text
    assert pending_view.json()["status"] == "pending"
    assert pending_view.json()["reason"] == "Ready to move forward"

    # Company cannot see the identity before the candidate approves.
    premature_view = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert premature_view.status_code == 400

    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert revealed_response.status_code == 200, revealed_response.text
    revealed = revealed_response.json()
    assert revealed["full_name"] == "Secret Applicant"
    assert revealed["email"] == "applicant@shadowreveal-approve.com"
    assert revealed["career_entries"][0]["company_name"] == "Stripe"

    application_status = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert application_status.json()[0]["status"] == "revealed"


async def test_candidate_can_decline_reveal_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-decline.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-decline.com"
    )

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    decline_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )
    assert decline_response.status_code == 200, decline_response.text
    assert decline_response.json()["status"] == "declined"

    still_hidden = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert still_hidden.status_code == 400

    # Responding twice is rejected — the decision is final.
    second_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert second_response.status_code == 400


async def test_reveal_request_scoped_to_owning_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-scope.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _owner_candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-scope.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    other_tokens = await candidate_signup(client, email="other@shadowreveal-scope.com")
    other_headers = auth_headers(other_tokens["access_token"])

    response = await client.get(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}", headers=other_headers
    )
    assert response.status_code == 404

from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, signup, step_up_headers

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
    save_response = await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Senior Product Leader",
            "summary": "A senior product leader.",
            "personal_info": {"legal_name": full_name},
            "career_entries": [],
        },
        headers=candidate_headers,
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


async def test_get_applicant_matches_the_list_entry(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-get.com", company_name="Applicant Get Co")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@applicant-get.com"
    )

    response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["application_id"] == application["id"]
    assert body["callsign"] == application["callsign"]
    assert body["effective_stage"] == "new"


async def test_get_applicant_404_wrong_job_application_pairing(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-get-404.com")
    headers = auth_headers(owner["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers)
    job_b_payload = {**_JOB_PAYLOAD, "title": "A Different Role"}
    job_b_response = await client.post("/api/v1/shadow-jobs", json=job_b_payload, headers=headers)
    assert job_b_response.status_code == 201
    job_b = job_b_response.json()
    publish_b = await client.post(f"/api/v1/shadow-jobs/mine/{job_b['id']}/publish", headers=headers)
    assert publish_b.status_code == 200

    application, _ = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate@applicant-get-404.com"
    )

    response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job_b['id']}/applicants/{application['id']}", headers=headers
    )
    assert response.status_code == 404


async def test_applicant_match_computes_and_caches(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-match.com", company_name="Match Co")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@applicant-match.com"
    )

    first = await client.get(
        f"/api/v1/matches/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["match_tier"] == "Strong Match"
    assert body["match_score"] == 72
    assert body["strengths"] == ["Fake strength: relevant skills overlap"]
    assert body["gaps"] == ["Fake gap: limited seniority evidence"]

    # Second call must be a cache hit, not a second LLM call -- flip the fake to prove it.
    second = await client.get(
        f"/api/v1/matches/mine/{job['id']}/applicants/{application['id']}", headers=headers
    )
    assert second.status_code == 200, second.text
    assert second.json()["match_tier"] == "Strong Match"
    assert second.json()["generated_at"] == body["generated_at"]


async def test_applicant_match_cross_tenant_isolation(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@applicant-match-a.com", company_name="Match A")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate@applicant-match-a.com"
    )

    owner_b = await signup(client, email="owner@applicant-match-b.com", company_name="Match B")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get(
        f"/api/v1/matches/mine/{job_a['id']}/applicants/{application['id']}", headers=headers_b
    )
    assert response.status_code == 404


async def test_applicant_notes_create_and_list(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-notes.com", company_name="Notes Co")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@applicant-notes.com"
    )

    empty = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/notes",
        headers=headers,
    )
    assert empty.status_code == 200, empty.text
    assert empty.json() == []

    create_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/notes",
        json={"body": "Strong domain background, worth an early interview."},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    note = create_response.json()
    assert note["body"] == "Strong domain background, worth an early interview."
    assert note["author_email"] == "owner@applicant-notes.com"

    list_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/notes",
        headers=headers,
    )
    assert list_response.status_code == 200, list_response.text
    notes = list_response.json()
    assert len(notes) == 1
    assert notes[0]["id"] == note["id"]


async def test_applicant_notes_never_visible_to_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-notes-priv.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@applicant-notes-priv.com"
    )

    create_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/notes",
        json={"body": "Internal-only note."},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text

    # No candidate-facing route exists for notes at all -- confirm the company-only path 401s a
    # candidate token outright rather than merely filtering results.
    candidate_attempt = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/notes",
        headers=candidate_headers,
    )
    assert candidate_attempt.status_code == 401


async def test_applicant_activity_lists_real_events(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@applicant-activity.com", company_name="Activity Co")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@applicant-activity.com"
    )

    message_response = await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "Thanks for applying — we'll be in touch."},
        headers=headers,
    )
    assert message_response.status_code == 201, message_response.text

    reveal_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Hiring Manager Interview"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 201, reveal_response.text

    respond_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text

    activity_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/activity",
        headers=headers,
    )
    assert activity_response.status_code == 200, activity_response.text
    actions = [entry["action"] for entry in activity_response.json()]
    assert "shadow_application.submitted" in actions
    assert "message.sent" in actions
    assert "shadow_reveal.requested" in actions
    assert "shadow_reveal.approved" in actions


async def test_applicant_activity_cross_tenant_isolation(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@applicant-activity-a.com", company_name="Act A")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate@applicant-activity-a.com"
    )

    owner_b = await signup(client, email="owner@applicant-activity-b.com", company_name="Act B")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job_a['id']}/applicants/{application['id']}/activity",
        headers=headers_b,
    )
    assert response.status_code == 404

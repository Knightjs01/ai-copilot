from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, signup

_JOB_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "summary": "Own our core platform services.",
    "description": "A full description of the role and its responsibilities.",
}


def _future_iso(*, days: int = 3) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


async def _create_and_publish_job(client: AsyncClient, *, headers: dict) -> dict:
    response = await client.post("/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=headers)
    assert response.status_code == 201, response.text
    job = response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def _build_and_approve_passport(
    client: AsyncClient, *, email: str, full_name: str = "Jamie Candidate"
) -> dict:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    payload = {
        "headline": "Senior Backend Engineer",
        "summary": "Backend engineer with experience building scalable services.",
        "skills": ["Backend Development"],
        "personal_info": {"legal_name": full_name},
        "career_entries": [],
    }
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=payload, headers=candidate_headers
    )
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    return candidate_headers


async def _apply(client: AsyncClient, *, job_id: str, candidate_headers: dict) -> dict:
    response = await client.post(
        f"/api/v1/shadow-jobs/board/{job_id}/apply", headers=candidate_headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_search_jobs_routes_and_returns_filters(client: AsyncClient) -> None:
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-search.com"
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "search for remote roles", "context_type": "none"},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "search_jobs"
    assert body["board_filters"]["remote_preference"] == "remote"


async def test_explain_match_with_job_context_and_approved_passport(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@copilot-match.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-match.com"
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "how well do I match this?",
            "context_type": "job",
            "context_id": job["id"],
        },
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "explain_match"
    assert body["match"]["match_tier"] == "Strong Match"


async def test_explain_match_without_job_context_nudges(client: AsyncClient) -> None:
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-match-nocontext.com"
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "how well do I match this?", "context_type": "none"},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "reply"
    assert "open a specific job" in body["reply"].lower()


async def test_suggest_improvements_returns_real_suggestion(client: AsyncClient) -> None:
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-improve.com"
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "how can I improve my summary?", "context_type": "passport"},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "suggest_improvements"
    assert body["suggested_summary"]


async def test_summarize_applications_with_and_without_context(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@copilot-summary.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-summary.com"
    )
    application = await _apply(client, job_id=job["id"], candidate_headers=candidate_headers)

    portfolio_response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "what's the status of my applications?", "context_type": "none"},
        headers=candidate_headers,
    )
    assert portfolio_response.status_code == 200, portfolio_response.text
    portfolio_body = portfolio_response.json()
    assert portfolio_body["action"] == "summarize_applications"
    assert job["title"] in portfolio_body["reply"]

    single_response = await client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "what's the status of this application?",
            "context_type": "application",
            "context_id": application["id"],
        },
        headers=candidate_headers,
    )
    assert single_response.status_code == 200, single_response.text
    single_body = single_response.json()
    assert single_body["action"] == "summarize_applications"
    assert job["title"] in single_body["reply"]


async def test_interview_prep_returns_real_questions(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@copilot-prep.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    candidate_headers = await _build_and_approve_passport(
        client, email="candidate@copilot-prep.com"
    )
    application = await _apply(client, job_id=job["id"], candidate_headers=candidate_headers)

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=owner_headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text
    interview_id = schedule_response.json()["id"]

    response = await client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "help me prep for this interview",
            "context_type": "interview",
            "context_id": interview_id,
        },
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "interview_prep"
    assert len(body["interview_prep_questions"]) == 2


async def test_interview_prep_on_another_candidates_interview_is_404(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@copilot-isolation.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    candidate_a_headers = await _build_and_approve_passport(
        client, email="candidate-a@copilot-isolation.com"
    )
    application = await _apply(client, job_id=job["id"], candidate_headers=candidate_a_headers)
    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=owner_headers,
    )
    interview_id = schedule_response.json()["id"]

    candidate_b_headers = await _build_and_approve_passport(
        client, email="candidate-b@copilot-isolation.com"
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "help me prep for this interview",
            "context_type": "interview",
            "context_id": interview_id,
        },
        headers=candidate_b_headers,
    )
    assert response.status_code == 404


async def test_greeting_routes_to_reply(client: AsyncClient) -> None:
    candidate_headers = await _build_and_approve_passport(client, email="candidate@copilot-hi.com")

    response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "hi there", "context_type": "none"},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"] == "reply"
    assert body["reply"]

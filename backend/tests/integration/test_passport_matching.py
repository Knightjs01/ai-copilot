from httpx import AsyncClient

from tests.conftest import FakePassportMatchingLLMClient
from tests.integration.helpers import auth_headers, candidate_signup, signup

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


async def _create_and_publish_job(client: AsyncClient, *, headers: dict) -> dict:
    create_response = await client.post("/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=headers)
    assert create_response.status_code == 201, create_response.text
    job = create_response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def _build_and_approve_passport(
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
    save_response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert approve_response.status_code == 200, approve_response.text
    return approve_response.json()


async def test_match_is_computed_and_cached_on_second_read(
    client: AsyncClient, fake_passport_matching_llm_client: FakePassportMatchingLLMClient
) -> None:
    owner = await signup(client, email="owner@matching-cache.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@matching-cache.com")
    candidate_headers = auth_headers(candidate["access_token"])
    await _build_and_approve_passport(client, headers=candidate_headers)

    first = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_headers)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["job_id"] == job["id"]
    assert body["match_tier"] == "Strong Match"
    assert body["match_score"] == 72
    assert body["strengths"] == ["Fake strength: relevant skills overlap"]
    assert len(fake_passport_matching_llm_client.score_calls) == 1

    second = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_headers)
    assert second.status_code == 200, second.text
    # Cache hit -- no second LLM call for the same (passport_version, job) pair.
    assert len(fake_passport_matching_llm_client.score_calls) == 1


async def test_match_recomputes_after_job_is_updated(
    client: AsyncClient, fake_passport_matching_llm_client: FakePassportMatchingLLMClient
) -> None:
    owner_headers = auth_headers(
        (await signup(client, email="owner@matching-stale.com"))["access_token"]
    )
    job = await _create_and_publish_job(client, headers=owner_headers)

    candidate_headers = auth_headers(
        (await candidate_signup(client, email="candidate@matching-stale.com"))["access_token"]
    )
    await _build_and_approve_passport(client, headers=candidate_headers)

    first = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_headers)
    assert first.status_code == 200, first.text
    assert len(fake_passport_matching_llm_client.score_calls) == 1

    update_response = await client.patch(
        f"/api/v1/shadow-jobs/mine/{job['id']}",
        json={"title": "Staff Product Designer II"},
        headers=owner_headers,
    )
    assert update_response.status_code == 200, update_response.text

    second = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_headers)
    assert second.status_code == 200, second.text
    # The job changed since the cached row was computed -- a fresh compute is required.
    assert len(fake_passport_matching_llm_client.score_calls) == 2


async def test_match_requires_an_approved_passport(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@matching-noapproval.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@matching-noapproval.com")
    response = await client.get(
        f"/api/v1/matches/{job['id']}", headers=auth_headers(candidate["access_token"])
    )
    assert response.status_code == 400, response.text


async def test_batch_matches_returns_scores_for_each_job(
    client: AsyncClient, fake_passport_matching_llm_client: FakePassportMatchingLLMClient
) -> None:
    owner_headers = auth_headers(
        (await signup(client, email="owner@matching-batch.com"))["access_token"]
    )
    job_a = await _create_and_publish_job(client, headers=owner_headers)
    job_b_payload = {**_JOB_PAYLOAD, "title": "Backend Engineer"}
    create_b = await client.post("/api/v1/shadow-jobs", json=job_b_payload, headers=owner_headers)
    assert create_b.status_code == 201, create_b.text
    publish_b = await client.post(
        f"/api/v1/shadow-jobs/mine/{create_b.json()['id']}/publish", headers=owner_headers
    )
    job_b = publish_b.json()

    candidate_headers = auth_headers(
        (await candidate_signup(client, email="candidate@matching-batch.com"))["access_token"]
    )
    await _build_and_approve_passport(client, headers=candidate_headers)

    response = await client.post(
        "/api/v1/matches/batch",
        json={"shadow_job_ids": [job_a["id"], job_b["id"]]},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert {r["job_id"] for r in results} == {job_a["id"], job_b["id"]}
    assert len(fake_passport_matching_llm_client.score_calls) == 2

    # Re-requesting the same batch is fully cache-hit -- no new LLM calls.
    second = await client.post(
        "/api/v1/matches/batch",
        json={"shadow_job_ids": [job_a["id"], job_b["id"]]},
        headers=candidate_headers,
    )
    assert second.status_code == 200, second.text
    assert len(fake_passport_matching_llm_client.score_calls) == 2


async def test_batch_rejects_more_than_24_jobs(client: AsyncClient) -> None:
    candidate = await candidate_signup(client, email="candidate@matching-cap.com")
    candidate_headers = auth_headers(candidate["access_token"])
    await _build_and_approve_passport(client, headers=candidate_headers)

    fake_job_ids = [str(__import__("uuid").uuid4()) for _ in range(25)]
    response = await client.post(
        "/api/v1/matches/batch", json={"shadow_job_ids": fake_job_ids}, headers=candidate_headers
    )
    assert response.status_code in (400, 422), response.text


async def test_matches_are_isolated_per_candidate(
    client: AsyncClient, fake_passport_matching_llm_client: FakePassportMatchingLLMClient
) -> None:
    owner_headers = auth_headers(
        (await signup(client, email="owner@matching-isolation.com"))["access_token"]
    )
    job = await _create_and_publish_job(client, headers=owner_headers)

    candidate_a_headers = auth_headers(
        (await candidate_signup(client, email="candidate-a@matching-isolation.com"))["access_token"]
    )
    candidate_b_headers = auth_headers(
        (await candidate_signup(client, email="candidate-b@matching-isolation.com"))["access_token"]
    )
    await _build_and_approve_passport(client, headers=candidate_a_headers, headline="Engineer A")
    await _build_and_approve_passport(client, headers=candidate_b_headers, headline="Engineer B")

    response_a = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_a_headers)
    response_b = await client.get(f"/api/v1/matches/{job['id']}", headers=candidate_b_headers)
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    # Two distinct passport_version_ids -- each candidate's request is its own cache miss and
    # its own LLM call, not shared across candidates.
    assert len(fake_passport_matching_llm_client.score_calls) == 2


async def test_search_query_is_parsed_into_board_filters(
    client: AsyncClient, fake_passport_matching_llm_client: FakePassportMatchingLLMClient
) -> None:
    candidate = await candidate_signup(client, email="candidate@matching-search.com")
    candidate_headers = auth_headers(candidate["access_token"])
    await _build_and_approve_passport(client, headers=candidate_headers)

    response = await client.post(
        "/api/v1/matches/search",
        json={"query": "remote senior roles"},
        headers=candidate_headers,
    )
    assert response.status_code == 200, response.text
    filters = response.json()
    assert filters["remote_preference"] == "remote"
    assert fake_passport_matching_llm_client.search_calls == ["remote senior roles"]

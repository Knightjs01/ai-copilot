from httpx import AsyncClient

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


async def test_candidate_can_save_and_list_a_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-basic.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@savedjobs-basic.com")
    candidate_headers = auth_headers(candidate["access_token"])

    save_response = await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=candidate_headers
    )
    assert save_response.status_code == 201, save_response.text
    saved = save_response.json()
    assert saved["job"]["id"] == job["id"]
    assert saved["collection_name"] is None

    list_response = await client.get("/api/v1/saved-jobs", headers=candidate_headers)
    assert list_response.status_code == 200, list_response.text
    saved_jobs = list_response.json()
    assert len(saved_jobs) == 1
    assert saved_jobs[0]["job"]["title"] == _JOB_PAYLOAD["title"]


async def test_saving_the_same_job_twice_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-dup.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@savedjobs-dup.com")
    candidate_headers = auth_headers(candidate["access_token"])

    first = await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=candidate_headers
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=candidate_headers
    )
    assert second.status_code == 409, second.text


async def test_candidate_can_unsave_a_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-unsave.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@savedjobs-unsave.com")
    candidate_headers = auth_headers(candidate["access_token"])

    save_response = await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=candidate_headers
    )
    assert save_response.status_code == 201, save_response.text

    delete_response = await client.delete(
        f"/api/v1/saved-jobs/{job['id']}", headers=candidate_headers
    )
    assert delete_response.status_code == 204, delete_response.text

    list_response = await client.get("/api/v1/saved-jobs", headers=candidate_headers)
    assert list_response.json() == []

    # Unsaving something never saved (or already removed) 404s rather than silently no-opping.
    second_delete = await client.delete(
        f"/api/v1/saved-jobs/{job['id']}", headers=candidate_headers
    )
    assert second_delete.status_code == 404, second_delete.text


async def test_candidate_can_recollect_a_saved_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-collection.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate = await candidate_signup(client, email="candidate@savedjobs-collection.com")
    candidate_headers = auth_headers(candidate["access_token"])

    await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=candidate_headers
    )

    update_response = await client.patch(
        f"/api/v1/saved-jobs/{job['id']}",
        json={"collection_name": "Dream roles"},
        headers=candidate_headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["collection_name"] == "Dream roles"

    filtered = await client.get(
        "/api/v1/saved-jobs", params={"collection_name": "Dream roles"}, headers=candidate_headers
    )
    assert len(filtered.json()) == 1

    other_collection = await client.get(
        "/api/v1/saved-jobs", params={"collection_name": "Remote"}, headers=candidate_headers
    )
    assert other_collection.json() == []


async def test_saved_jobs_are_isolated_per_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-isolation.com")
    job = await _create_and_publish_job(client, headers=auth_headers(owner["access_token"]))

    candidate_a = await candidate_signup(client, email="candidate-a@savedjobs-isolation.com")
    candidate_b = await candidate_signup(client, email="candidate-b@savedjobs-isolation.com")
    headers_a = auth_headers(candidate_a["access_token"])
    headers_b = auth_headers(candidate_b["access_token"])

    save_response = await client.post(
        "/api/v1/saved-jobs", json={"shadow_job_id": job["id"]}, headers=headers_a
    )
    assert save_response.status_code == 201, save_response.text

    # Candidate B never saved it -- their list is empty and they can't unsave A's bookmark.
    list_b = await client.get("/api/v1/saved-jobs", headers=headers_b)
    assert list_b.json() == []

    delete_by_b = await client.delete(f"/api/v1/saved-jobs/{job['id']}", headers=headers_b)
    assert delete_by_b.status_code == 404, delete_by_b.text

    # Candidate A's bookmark is untouched.
    list_a = await client.get("/api/v1/saved-jobs", headers=headers_a)
    assert len(list_a.json()) == 1


async def test_cannot_save_an_unpublished_job(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@savedjobs-unpublished.com")
    create_response = await client.post(
        "/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=auth_headers(owner["access_token"])
    )
    assert create_response.status_code == 201, create_response.text
    draft_job = create_response.json()

    candidate = await candidate_signup(client, email="candidate@savedjobs-unpublished.com")
    save_response = await client.post(
        "/api/v1/saved-jobs",
        json={"shadow_job_id": draft_job["id"]},
        headers=auth_headers(candidate["access_token"]),
    )
    assert save_response.status_code == 404, save_response.text

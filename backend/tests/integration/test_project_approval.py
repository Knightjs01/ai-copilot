from httpx import AsyncClient

from tests.conftest import CapturingEmailSender, FakeHiringBlueprintLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup

_TOP_REQUIREMENTS = ["5+ years experience", "Strong communication skills"]


async def _make_project_ready(
    client: AsyncClient, *, headers: dict, title: str = "Senior Backend Engineer"
) -> str:
    project = await create_project(client, headers=headers, title=title)
    project_id = project["id"]

    await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"role_brief": "Looking for a senior backend engineer."},
        headers=headers,
    )
    blueprint_response = await client.post(
        f"/api/v1/projects/{project_id}/hiring-blueprint", headers=headers
    )
    assert blueprint_response.status_code == 200, blueprint_response.text
    alignment_response = await client.put(
        f"/api/v1/projects/{project_id}/hiring-manager-alignment",
        json={"top_requirements": _TOP_REQUIREMENTS},
        headers=headers,
    )
    assert alignment_response.status_code == 200, alignment_response.text
    return project_id


async def test_post_to_shadow_blocked_when_not_ready(
    client: AsyncClient, fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient
) -> None:
    owner = await signup(client, email="owner@approve1.com", company_name="Approve1 Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.post(
        f"/api/v1/projects/{project['id']}/post-to-shadow", headers=headers
    )
    assert response.status_code == 400, response.text
    assert "role brief" in response.json()["detail"]
    assert "Hiring Blueprint" in response.json()["detail"]
    assert "Hiring Manager Alignment" in response.json()["detail"]


async def test_save_as_draft_blocked_when_not_ready(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@approve2.com", company_name="Approve2 Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.post(f"/api/v1/projects/{project['id']}/save-as-draft", headers=headers)
    assert response.status_code == 400, response.text


async def test_post_to_shadow_creates_published_job_and_opens_project(
    client: AsyncClient, fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient
) -> None:
    owner = await signup(client, email="owner@approve3.com", company_name="Approve3 Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _make_project_ready(client, headers=headers)

    response = await client.post(f"/api/v1/projects/{project_id}/post-to-shadow", headers=headers)
    assert response.status_code == 200, response.text
    project = response.json()
    assert project["status"] == "open"

    jobs_response = await client.get("/api/v1/shadow-jobs/mine", headers=headers)
    assert jobs_response.status_code == 200
    jobs = [j for j in jobs_response.json() if j["project_id"] == project_id]
    assert len(jobs) == 1
    job = jobs[0]
    assert job["status"] == "published"
    assert job["title"] == "Senior Backend Engineer"
    assert job["summary"] == "A fake but deterministic role summary for testing."
    assert job["description"] == "Looking for a senior backend engineer."
    assert job["requirements"] == ["Fake required skill"]


async def test_post_to_shadow_twice_updates_same_job_not_a_duplicate(
    client: AsyncClient, fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient
) -> None:
    owner = await signup(client, email="owner@approve4.com", company_name="Approve4 Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _make_project_ready(client, headers=headers)

    first = await client.post(f"/api/v1/projects/{project_id}/post-to-shadow", headers=headers)
    assert first.status_code == 200, first.text

    # Edit the role brief, then re-approve — must update the same ShadowJob in place, never
    # create a second one (ShadowJob.project_id is hard-unique).
    await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"role_brief": "Updated role brief for the same role."},
        headers=headers,
    )
    second = await client.post(f"/api/v1/projects/{project_id}/post-to-shadow", headers=headers)
    assert second.status_code == 200, second.text

    jobs_response = await client.get("/api/v1/shadow-jobs/mine", headers=headers)
    jobs = [j for j in jobs_response.json() if j["project_id"] == project_id]
    assert len(jobs) == 1
    assert jobs[0]["description"] == "Updated role brief for the same role."


async def test_save_as_draft_never_creates_shadow_job(
    client: AsyncClient, fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient
) -> None:
    owner = await signup(client, email="owner@approve5.com", company_name="Approve5 Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _make_project_ready(client, headers=headers)

    response = await client.post(f"/api/v1/projects/{project_id}/save-as-draft", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "open"

    jobs_response = await client.get("/api/v1/shadow-jobs/mine", headers=headers)
    jobs = [j for j in jobs_response.json() if j["project_id"] == project_id]
    assert jobs == []


async def test_approve_routes_permission_gated(
    client: AsyncClient,
    sent_emails: CapturingEmailSender,
    fake_hiring_blueprint_llm_client: FakeHiringBlueprintLLMClient,
) -> None:
    owner = await signup(client, email="owner@approve6.com", company_name="Approve6 Co")
    owner_headers = auth_headers(owner["access_token"])
    project_id = await _make_project_ready(client, headers=owner_headers)

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@approve6.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])

    post_denied = await client.post(
        f"/api/v1/projects/{project_id}/post-to-shadow", headers=recruiter_headers
    )
    assert post_denied.status_code == 403

    draft_denied = await client.post(
        f"/api/v1/projects/{project_id}/save-as-draft", headers=recruiter_headers
    )
    assert draft_denied.status_code == 403

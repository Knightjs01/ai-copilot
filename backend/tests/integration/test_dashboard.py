from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup, create_project, signup
from tests.integration.test_prescreen_assessment import (
    _create_candidate_with_intelligence_pack,
    _setup_project_with_blueprint_and_alignment,
)

_JOB_PAYLOAD = {
    "title": "Staff Product Designer",
    "summary": "Own product design for our core platform.",
    "description": "A full description of the role and its responsibilities.",
}


async def _create_and_publish_job(
    client: AsyncClient, *, headers: dict, project_id: str | None = None
) -> dict:
    payload = {**_JOB_PAYLOAD, "project_id": project_id} if project_id else _JOB_PAYLOAD
    response = await client.post("/api/v1/shadow-jobs", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    job = response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def _apply_and_get_reveal_response(
    client: AsyncClient, *, headers: dict, job_id: str, email: str, approve: bool
) -> dict:
    tokens = await candidate_signup(client, email=email, full_name="Jamie Candidate")
    candidate_headers = auth_headers(tokens["access_token"])
    save_response = await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Senior Product Leader",
            "summary": "A senior product leader.",
            "personal_info": {"legal_name": "Jamie Candidate"},
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
    application = apply_response.json()

    request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job_id}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text

    respond_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": approve},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text
    return application


async def _create_candidate(
    client: AsyncClient, *, headers: dict, project_id: str, full_name: str, **extra: object
) -> dict:
    response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": full_name, **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_dashboard_counts_live_projects_and_pipeline_stages(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@dashboard.com", company_name="Dashboard Co")
    headers = auth_headers(owner["access_token"])

    open_project = await create_project(client, headers=headers, title="Open Role")
    cancelled_project = await create_project(client, headers=headers, title="Cancelled Role")
    cancel_response = await client.patch(
        f"/api/v1/projects/{cancelled_project['id']}",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert cancel_response.status_code == 200, cancel_response.text

    screening_candidate = await _create_candidate(
        client, headers=headers, project_id=open_project["id"], full_name="Screening One"
    )
    await client.patch(
        f"/api/v1/candidates/{screening_candidate['id']}",
        json={"status": "screening"},
        headers=headers,
    )

    interviewing_candidate = await _create_candidate(
        client, headers=headers, project_id=open_project["id"], full_name="Interviewing One"
    )
    await client.patch(
        f"/api/v1/candidates/{interviewing_candidate['id']}",
        json={"status": "interviewing"},
        headers=headers,
    )

    hired_candidate = await _create_candidate(
        client, headers=headers, project_id=open_project["id"], full_name="Hired One"
    )
    await client.patch(
        f"/api/v1/candidates/{hired_candidate['id']}", json={"status": "hired"}, headers=headers
    )

    # Belongs to the cancelled project — must not count toward candidates_in_process even though
    # its own status is still "new".
    await _create_candidate(
        client, headers=headers, project_id=cancelled_project["id"], full_name="Orphaned"
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["live_projects"] == 1
    # screening + interviewing + the cancelled-project "new" candidate (still non-terminal) = 3
    assert data["candidates_in_process"] == 3
    assert data["prescreen_stage_count"] == 1
    assert data["hiring_manager_stage_count"] == 1


async def test_dashboard_flags_candidate_needing_prescreen(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@dash-prescreen.com", company_name="Dash Prescreen Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Needs Prescreen Role")
    candidate = await _create_candidate(
        client, headers=headers, project_id=project["id"], full_name="Waiting Candidate"
    )
    await client.patch(
        f"/api/v1/candidates/{candidate['id']}", json={"status": "screening"}, headers=headers
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    action_items = response.json()["action_items"]

    matches = [item for item in action_items if item["candidate_id"] == candidate["id"]]
    assert len(matches) == 1
    assert matches[0]["type"] == "needs_prescreen"


async def test_dashboard_flags_candidate_ready_to_advance(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@dash-advance.com", company_name="Dash Advance Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="Advance Candidate"
    )
    assessment_response = await client.post(
        f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers
    )
    assert assessment_response.status_code == 200, assessment_response.text
    await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={"status": "screening", "prescreen_outcome": "advance"},
        headers=headers,
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    action_items = response.json()["action_items"]

    matches = [item for item in action_items if item["candidate_id"] == candidate_id]
    assert len(matches) == 1
    assert matches[0]["type"] == "ready_to_advance"


async def test_dashboard_flags_candidate_needing_interview_scheduling(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@dash-interview.com", company_name="Dash Interview Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Needs Interview Role")
    candidate = await _create_candidate(
        client, headers=headers, project_id=project["id"], full_name="Interview Candidate"
    )
    await client.patch(
        f"/api/v1/candidates/{candidate['id']}", json={"status": "interviewing"}, headers=headers
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    action_items = response.json()["action_items"]

    matches = [item for item in action_items if item["candidate_id"] == candidate["id"]]
    assert len(matches) == 1
    assert matches[0]["type"] == "needs_interview_scheduling"


async def test_dashboard_flags_project_missing_hiring_manager_alignment(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@dash-alignment.com", company_name="Dash Alignment Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Needs Alignment Role")

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    action_items = response.json()["action_items"]

    matches = [item for item in action_items if item["project_id"] == project["id"]]
    assert len(matches) == 1
    assert matches[0]["type"] == "needs_alignment"
    assert matches[0]["candidate_id"] is None


async def test_dashboard_project_id_filter_scopes_to_one_role(client: AsyncClient) -> None:
    """Powers Role Health: an optional project_id query param scopes the whole response to one
    project, and -- unlike the company-wide call -- does not truncate action_items at
    _MAX_ACTION_ITEMS, since a single role's real gap count should never be silently cut."""
    owner = await signup(client, email="owner@dash-scoped.com", company_name="Dash Scoped Co")
    headers = auth_headers(owner["access_token"])

    role_a = await create_project(client, headers=headers, title="Role A")
    role_b = await create_project(client, headers=headers, title="Role B")
    # Neither role has a hiring manager alignment submitted -- both would show a real
    # needs_alignment gap in the company-wide view.

    scoped_response = await client.get(
        "/api/v1/dashboard", params={"project_id": role_a["id"]}, headers=headers
    )
    assert scoped_response.status_code == 200, scoped_response.text
    scoped = scoped_response.json()

    assert scoped["live_projects"] == 1
    assert all(item["project_id"] == role_a["id"] for item in scoped["action_items"])
    assert any(item["type"] == "needs_alignment" for item in scoped["action_items"])
    # Role B's own real gap must not leak into a request scoped to Role A.
    assert not any(item["project_id"] == role_b["id"] for item in scoped["action_items"])


async def test_dashboard_is_scoped_to_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@dash-tenant-a.com", company_name="Dash Tenant A")
    headers_a = auth_headers(owner_a["access_token"])
    await create_project(client, headers=headers_a, title="Tenant A Role")

    owner_b = await signup(client, email="owner@dash-tenant-b.com", company_name="Dash Tenant B")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get("/api/v1/dashboard", headers=headers_b)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["live_projects"] == 0
    assert data["action_items"] == []


async def test_dashboard_surfaces_unseen_reveal_response_and_clears_once_viewed(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@dashboard-reveal.com", company_name="Reveal Dash Co")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application = await _apply_and_get_reveal_response(
        client,
        headers=headers,
        job_id=job["id"],
        email="candidate@dashboard-reveal.com",
        approve=True,
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    items = response.json()["action_items"]
    reveal_items = [i for i in items if i["type"] == "reveal_response_needs_review"]
    assert len(reveal_items) == 1
    item = reveal_items[0]
    assert item["shadow_job_id"] == job["id"]
    assert item["application_id"] == application["id"]
    assert application["callsign"] in item["message"]
    assert "approved" in item["message"]

    mark_viewed = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/mark-viewed",
        headers=headers,
    )
    assert mark_viewed.status_code == 200, mark_viewed.text

    after_viewed = await client.get("/api/v1/dashboard", headers=headers)
    remaining = [
        i
        for i in after_viewed.json()["action_items"]
        if i["type"] == "reveal_response_needs_review"
    ]
    assert remaining == []


async def test_dashboard_reveal_action_item_scoped_to_project(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@dashboard-reveal-scope.com")
    headers = auth_headers(owner["access_token"])
    project_a = await create_project(client, headers=headers, title="Project A")
    project_b = await create_project(client, headers=headers, title="Project B")
    job_a = await _create_and_publish_job(client, headers=headers, project_id=project_a["id"])
    job_b = await _create_and_publish_job(client, headers=headers, project_id=project_b["id"])
    await _apply_and_get_reveal_response(
        client,
        headers=headers,
        job_id=job_a["id"],
        email="candidate@dashboard-reveal-scope-a.com",
        approve=True,
    )
    await _apply_and_get_reveal_response(
        client,
        headers=headers,
        job_id=job_b["id"],
        email="candidate@dashboard-reveal-scope-b.com",
        approve=False,
    )

    scoped = await client.get(f"/api/v1/dashboard?project_id={project_a['id']}", headers=headers)
    assert scoped.status_code == 200, scoped.text
    reveal_items = [
        i for i in scoped.json()["action_items"] if i["type"] == "reveal_response_needs_review"
    ]
    assert len(reveal_items) == 1
    assert reveal_items[0]["shadow_job_id"] == job_a["id"]

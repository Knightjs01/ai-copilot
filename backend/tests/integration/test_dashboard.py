from httpx import AsyncClient

from tests.integration.helpers import auth_headers, create_project, signup
from tests.integration.test_prescreen_assessment import (
    _create_candidate_with_intelligence_pack,
    _setup_project_with_blueprint_and_alignment,
)


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

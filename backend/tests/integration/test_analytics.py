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


async def test_analytics_aggregates_source_status_and_salary(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@analytics.com", company_name="Analytics Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    project_id = project["id"]

    direct_one = await _create_candidate(
        client, headers=headers, project_id=project_id, full_name="Direct One", source="direct"
    )
    await client.patch(
        f"/api/v1/candidates/{direct_one['id']}",
        json={
            "expected_salary": 80000,
            "status": "screening",
            "location": "Leeds, UK",
            "notice_period": "one_month",
            "current_employer": "Acme Corp",
        },
        headers=headers,
    )

    agency_one = await _create_candidate(
        client, headers=headers, project_id=project_id, full_name="Agency One", source="agency"
    )
    await client.patch(
        f"/api/v1/candidates/{agency_one['id']}",
        json={
            "agency_name": "Talent Partners",
            "expected_salary": 100000,
            "location": "Leeds, UK",
            "notice_period": "immediate",
        },
        headers=headers,
    )

    agency_two = await _create_candidate(
        client, headers=headers, project_id=project_id, full_name="Agency Two", source="agency"
    )
    await client.patch(
        f"/api/v1/candidates/{agency_two['id']}",
        json={"agency_name": "Talent Partners"},
        headers=headers,
    )

    # No salary set, deliberately, to prove salary_stats only averages over candidates that
    # actually have one — it shouldn't be treated as zero.
    await _create_candidate(
        client, headers=headers, project_id=project_id, full_name="No Salary Set", source="direct"
    )

    response = await client.get(f"/api/v1/projects/{project_id}/analytics", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_candidates"] == 4
    assert data["status_breakdown"]["screening"] == 1
    assert data["status_breakdown"]["new"] == 3
    assert data["source_breakdown"]["direct"] == 2
    assert data["source_breakdown"]["agency"] == 2
    assert data["agency_breakdown"] == {"Talent Partners": 2}
    assert data["salary_stats"]["count"] == 2
    assert data["salary_stats"]["average"] == 90000
    assert data["salary_stats"]["minimum"] == 80000
    assert data["salary_stats"]["maximum"] == 100000
    assert data["location_breakdown"] == {"Leeds, UK": 2}
    assert data["notice_period_breakdown"] == {"one_month": 1, "immediate": 1}
    assert data["current_employer_breakdown"] == {"Acme Corp": 1}


async def test_analytics_includes_fit_rating_and_prescreen_outcome(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@analytics-fit.com", company_name="Analytics Fit Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _setup_project_with_blueprint_and_alignment(client, headers=headers)
    candidate_id = await _create_candidate_with_intelligence_pack(
        client, headers=headers, project_id=project_id, full_name="Fit Candidate"
    )
    await client.post(f"/api/v1/candidates/{candidate_id}/prescreen-assessment", headers=headers)
    await client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={"prescreen_outcome": "advance"},
        headers=headers,
    )

    response = await client.get(f"/api/v1/projects/{project_id}/analytics", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["fit_rating_breakdown"] == {"Good Fit": 1}
    assert data["prescreen_outcome_breakdown"] == {"advance": 1}


async def test_analytics_for_missing_project_is_404(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@analytics-404.com", company_name="Analytics 404 Co")
    headers = auth_headers(owner["access_token"])

    response = await client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/analytics", headers=headers
    )
    assert response.status_code == 404

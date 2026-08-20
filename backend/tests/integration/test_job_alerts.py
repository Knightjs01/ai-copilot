from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, signup

_JOB_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "employment_type": "full_time",
    "remote_preference": "remote",
    "summary": "Own our core platform services.",
    "description": "A full description of the role and its responsibilities.",
}


async def _create_and_publish_job(client: AsyncClient, *, headers: dict, **overrides) -> dict:
    payload = {**_JOB_PAYLOAD, **overrides}
    create_response = await client.post("/api/v1/shadow-jobs", json=payload, headers=headers)
    assert create_response.status_code == 201, create_response.text
    job = create_response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def test_candidate_can_create_list_update_delete_an_alert(client: AsyncClient) -> None:
    candidate = await candidate_signup(client, email="candidate@jobalerts-crud.com")
    headers = auth_headers(candidate["access_token"])

    create_response = await client.post(
        "/api/v1/job-alerts",
        json={"name": "Remote roles", "remote_preference": "remote"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    alert = create_response.json()
    assert alert["name"] == "Remote roles"
    assert alert["is_active"] is True

    list_response = await client.get("/api/v1/job-alerts", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = await client.patch(
        f"/api/v1/job-alerts/{alert['id']}", json={"is_active": False}, headers=headers
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["is_active"] is False

    delete_response = await client.delete(f"/api/v1/job-alerts/{alert['id']}", headers=headers)
    assert delete_response.status_code == 204, delete_response.text
    assert (await client.get("/api/v1/job-alerts", headers=headers)).json() == []


async def test_alerts_are_isolated_per_candidate(client: AsyncClient) -> None:
    candidate_a = await candidate_signup(client, email="candidate-a@jobalerts-isolation.com")
    candidate_b = await candidate_signup(client, email="candidate-b@jobalerts-isolation.com")
    headers_a = auth_headers(candidate_a["access_token"])
    headers_b = auth_headers(candidate_b["access_token"])

    create_response = await client.post(
        "/api/v1/job-alerts", json={"remote_preference": "remote"}, headers=headers_a
    )
    alert = create_response.json()

    assert (await client.get("/api/v1/job-alerts", headers=headers_b)).json() == []
    delete_by_b = await client.delete(f"/api/v1/job-alerts/{alert['id']}", headers=headers_b)
    assert delete_by_b.status_code == 404
    update_by_b = await client.patch(
        f"/api/v1/job-alerts/{alert['id']}", json={"is_active": False}, headers=headers_b
    )
    assert update_by_b.status_code == 404


async def test_empty_criteria_alert_is_rejected(client: AsyncClient) -> None:
    candidate = await candidate_signup(client, email="candidate@jobalerts-empty.com")
    headers = auth_headers(candidate["access_token"])

    response = await client.post("/api/v1/job-alerts", json={"name": "Anything"}, headers=headers)
    assert response.status_code == 400, response.text


async def test_alert_limit_is_enforced(client: AsyncClient) -> None:
    candidate = await candidate_signup(client, email="candidate@jobalerts-limit.com")
    headers = auth_headers(candidate["access_token"])

    for i in range(10):
        response = await client.post(
            "/api/v1/job-alerts", json={"location": f"City {i}"}, headers=headers
        )
        assert response.status_code == 201, response.text

    over_limit = await client.post(
        "/api/v1/job-alerts", json={"location": "One too many"}, headers=headers
    )
    assert over_limit.status_code == 400, over_limit.text


async def test_publishing_a_matching_job_sends_exactly_one_email_for_overlapping_alerts(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@jobalerts-notify.com")
    owner_headers = auth_headers(owner["access_token"])

    candidate = await candidate_signup(client, email="candidate@jobalerts-notify.com")
    candidate_headers = auth_headers(candidate["access_token"])

    await client.post(
        "/api/v1/job-alerts",
        json={"name": "Remote roles", "remote_preference": "remote"},
        headers=candidate_headers,
    )
    await client.post(
        "/api/v1/job-alerts",
        json={"name": "Full-time roles", "employment_type": "full_time"},
        headers=candidate_headers,
    )

    sent_emails.sent.clear()
    await _create_and_publish_job(client, headers=owner_headers)

    matching_sends = [e for e in sent_emails.sent if e["to"] == "candidate@jobalerts-notify.com"]
    assert len(matching_sends) == 1, sent_emails.sent


async def test_non_matching_job_sends_no_email(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@jobalerts-nomatch.com")
    owner_headers = auth_headers(owner["access_token"])

    candidate = await candidate_signup(client, email="candidate@jobalerts-nomatch.com")
    candidate_headers = auth_headers(candidate["access_token"])

    await client.post(
        "/api/v1/job-alerts", json={"location": "A place this job isn't"}, headers=candidate_headers
    )

    sent_emails.sent.clear()
    await _create_and_publish_job(client, headers=owner_headers)

    matching_sends = [e for e in sent_emails.sent if e["to"] == "candidate@jobalerts-nomatch.com"]
    assert matching_sends == []


async def test_paused_alert_never_matches(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@jobalerts-paused.com")
    owner_headers = auth_headers(owner["access_token"])

    candidate = await candidate_signup(client, email="candidate@jobalerts-paused.com")
    candidate_headers = auth_headers(candidate["access_token"])

    create_response = await client.post(
        "/api/v1/job-alerts", json={"remote_preference": "remote"}, headers=candidate_headers
    )
    alert = create_response.json()
    await client.patch(
        f"/api/v1/job-alerts/{alert['id']}", json={"is_active": False}, headers=candidate_headers
    )

    sent_emails.sent.clear()
    await _create_and_publish_job(client, headers=owner_headers)

    matching_sends = [e for e in sent_emails.sent if e["to"] == "candidate@jobalerts-paused.com"]
    assert matching_sends == []

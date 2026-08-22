import uuid as uuid_module
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import text

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    candidate_signup,
    create_project,
    invite_and_accept,
    signup,
    step_up_headers,
)

_JOB_PAYLOAD = {
    "title": "Staff Product Designer",
    "summary": "Own product design for our core platform.",
    "description": "A full description of the role and its responsibilities.",
}


def _future_iso(*, days: int = 3) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


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


async def _apply_with_new_candidate(
    client: AsyncClient, *, job_id: str, email: str, full_name: str = "Jamie Candidate"
) -> tuple[dict, dict]:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    passport_payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader.",
        "personal_info": {"legal_name": full_name},
        "career_entries": [],
    }
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=passport_payload, headers=candidate_headers
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


async def _table_row_count(table: str, column: str, value: str, *, company_id: str) -> int:
    from app.db.base import engine

    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_id)}'")
            )
            result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE {column} = :value"),  # noqa: S608
                {"value": value},
            )
            return result.scalar_one()


async def test_company_schedules_and_candidate_sees_it(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-basic.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-basic.com"
    )

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={
            "scheduled_at": _future_iso(),
            "location": "Zoom",
            "meeting_link": "https://zoom.example.com/abc",
        },
        headers=owner_headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text
    interview = schedule_response.json()
    assert interview["status"] == "scheduled"
    assert interview["application_id"] == application["id"]

    candidate_list = await client.get("/api/v1/interviews", headers=candidate_headers)
    assert candidate_list.status_code == 200, candidate_list.text
    interviews = candidate_list.json()
    assert len(interviews) == 1
    assert interviews[0]["id"] == interview["id"]
    assert interviews[0]["job_title"] == job["title"]
    assert interviews[0]["callsign"] == application["callsign"]
    assert interviews[0]["meeting_link"] == "https://zoom.example.com/abc"

    company_list = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=owner_headers,
    )
    assert company_list.status_code == 200, company_list.text
    assert len(company_list.json()) == 1


async def test_schedule_emails_the_candidate(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(
        client, email="owner@interviews-notify.com", company_name="Notify Interviews Co"
    )
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-notify.com"
    )

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "location": "Zoom"},
        headers=owner_headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text

    assert len(sent_emails.sent) == 1
    email = sent_emails.sent[0]
    assert email["to"] == "candidate@interviews-notify.com"
    assert "Notify Interviews Co" in email["subject"]


async def test_reschedule_updates_time_for_both_sides(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-reschedule.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-reschedule.com"
    )

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(days=2)},
        headers=owner_headers,
    )
    interview_id = schedule_response.json()["id"]

    new_time = _future_iso(days=5)
    update_response = await client.patch(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}/{interview_id}",
        json={"scheduled_at": new_time},
        headers=owner_headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert datetime.fromisoformat(update_response.json()["scheduled_at"]) == datetime.fromisoformat(
        new_time
    )

    candidate_list = await client.get("/api/v1/interviews", headers=candidate_headers)
    assert datetime.fromisoformat(
        candidate_list.json()[0]["scheduled_at"]
    ) == datetime.fromisoformat(new_time)


async def test_cancel_and_complete_flip_status_on_both_sides(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-status.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-status.com"
    )

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=owner_headers,
    )
    interview_id = schedule_response.json()["id"]

    cancel_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}/{interview_id}/cancel",
        headers=owner_headers,
    )
    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "cancelled"

    candidate_list = await client.get("/api/v1/interviews", headers=candidate_headers)
    assert candidate_list.json()[0]["status"] == "cancelled"

    complete_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}/{interview_id}/complete",
        headers=owner_headers,
    )
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["status"] == "completed"


async def test_scheduling_in_the_past_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-pasttime.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-pasttime.com"
    )

    response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _past_iso()},
        headers=owner_headers,
    )
    assert response.status_code == 400


async def test_applicant_list_shows_upcoming_interview_flag(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-flag.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-flag.com"
    )

    before = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert before.json()[0]["has_upcoming_interview"] is False

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=owner_headers,
    )
    interview_id = schedule_response.json()["id"]

    after = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert after.json()[0]["has_upcoming_interview"] is True

    await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}/{interview_id}/cancel",
        headers=owner_headers,
    )
    cancelled = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert cancelled.json()[0]["has_upcoming_interview"] is False


async def test_interviewer_can_view_assigned_interview_but_not_schedule(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Interviewer has interviews.view but not interviews.schedule -- Recruiter (the old
    Member's successor) now has both, so it's Interviewer that exercises this view-only floor
    post-Phase-3. Assigned as a participant at schedule time so the view call actually surfaces
    the interview -- unassigned-Interviewer scoping gets its own dedicated coverage in
    test_interview_participants.py."""
    owner = await signup(client, email="owner@interviews-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-memberperm.com"
    )

    interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="interviewer@interviews-memberperm.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_headers = auth_headers(interviewer["access_token"])
    me_response = await client.get("/api/v1/auth/me", headers=interviewer_headers)
    interviewer_id = me_response.json()["id"]

    await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "interviewer_user_ids": [interviewer_id]},
        headers=owner_headers,
    )

    view_response = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=interviewer_headers,
    )
    assert view_response.status_code == 200, view_response.text
    assert len(view_response.json()) == 1

    schedule_denied = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(days=4)},
        headers=interviewer_headers,
    )
    assert schedule_denied.status_code == 403


async def test_cross_tenant_and_cross_candidate_isolation(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner-a@interviews-isolation.com")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)
    application_a, candidate_headers_a = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate-a@interviews-isolation.com"
    )
    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job_a['id']}/applicants/{application_a['id']}",
        json={"scheduled_at": _future_iso()},
        headers=headers_a,
    )
    interview_id = schedule_response.json()["id"]

    owner_b = await signup(client, email="owner-b@interviews-isolation-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    # Company B has no such job/application -- 404, not leaked data.
    cross_tenant_view = await client.get(
        f"/api/v1/interviews/mine/{job_a['id']}/applicants/{application_a['id']}",
        headers=headers_b,
    )
    assert cross_tenant_view.status_code == 404
    cross_tenant_cancel = await client.post(
        f"/api/v1/interviews/mine/{job_a['id']}/applicants/{application_a['id']}/{interview_id}/cancel",
        headers=headers_b,
    )
    assert cross_tenant_cancel.status_code == 404

    # Candidate B never applied to this job -- their own interview list stays empty.
    candidate_b_tokens = await candidate_signup(
        client, email="candidate-b@interviews-isolation.com"
    )
    candidate_headers_b = auth_headers(candidate_b_tokens["access_token"])
    candidate_b_list = await client.get("/api/v1/interviews", headers=candidate_headers_b)
    assert candidate_b_list.status_code == 200
    assert candidate_b_list.json() == []

    # Candidate A still sees their own interview correctly.
    candidate_a_list = await client.get("/api/v1/interviews", headers=candidate_headers_a)
    assert len(candidate_a_list.json()) == 1


async def test_company_wide_interview_list(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@interviews-companywide.com")
    owner_headers = auth_headers(owner["access_token"])
    job_a = await _create_and_publish_job(client, headers=owner_headers)
    application_a, _ = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate-a@interviews-companywide.com"
    )
    job_b = await _create_and_publish_job(client, headers=owner_headers)
    application_b, _ = await _apply_with_new_candidate(
        client, job_id=job_b["id"], email="candidate-b@interviews-companywide.com"
    )

    await client.post(
        f"/api/v1/interviews/mine/{job_a['id']}/applicants/{application_a['id']}",
        json={"scheduled_at": _future_iso(days=1)},
        headers=owner_headers,
    )
    await client.post(
        f"/api/v1/interviews/mine/{job_b['id']}/applicants/{application_b['id']}",
        json={"scheduled_at": _future_iso(days=2)},
        headers=owner_headers,
    )

    response = await client.get("/api/v1/interviews/mine", headers=owner_headers)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 2
    assert {r["job_title"] for r in rows} == {job_a["title"], job_b["title"]}
    assert rows[0]["scheduled_at"] < rows[1]["scheduled_at"]


async def test_company_wide_interview_list_scopes_interviewer_to_assigned(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@interviews-companywide-scope.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-companywide-scope.com"
    )
    interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="interviewer@interviews-companywide-scope.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_headers = auth_headers(interviewer["access_token"])

    # An interview this Interviewer is NOT assigned to.
    await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=owner_headers,
    )

    owner_view = await client.get("/api/v1/interviews/mine", headers=owner_headers)
    assert len(owner_view.json()) == 1

    interviewer_view = await client.get("/api/v1/interviews/mine", headers=interviewer_headers)
    assert interviewer_view.status_code == 200
    assert interviewer_view.json() == []


async def test_burn_project_purges_interviews(client: AsyncClient) -> None:
    owner = await signup(
        client, email="owner@interviews-burn.com", company_name="Burn Interviews Co"
    )
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers, title="Role With Interviews")
    project_id = project["id"]

    job = await _create_and_publish_job(client, headers=headers, project_id=project_id)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviews-burn.com"
    )
    await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso()},
        headers=headers,
    )

    assert (
        await _table_row_count(
            "interviews", "shadow_application_id", application["id"], company_id=company_id
        )
        == 1
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text
    categories = burn_response.json()["certificate"]["data_categories_destroyed"]
    assert "Scheduled interviews" in categories

    assert (
        await _table_row_count(
            "interviews", "shadow_application_id", application["id"], company_id=company_id
        )
        == 0
    )

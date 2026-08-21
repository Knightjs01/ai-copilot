from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, invite_and_accept, signup

_JOB_PAYLOAD = {
    "title": "Staff Product Designer",
    "summary": "Own product design for our core platform.",
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


async def _apply_with_new_candidate(
    client: AsyncClient, *, job_id: str, email: str, full_name: str = "Jamie Candidate"
) -> dict:
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
    return apply_response.json()


async def _get_user_id(client: AsyncClient, *, headers: dict) -> str:
    me = await client.get("/api/v1/auth/me", headers=headers)
    return me.json()["id"]


async def test_interviewer_sees_only_assigned_interviews(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@interviewparts.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviewparts.com"
    )

    assigned_interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="assigned@interviewparts.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    assigned_headers = auth_headers(assigned_interviewer["access_token"])
    assigned_id = await _get_user_id(client, headers=assigned_headers)

    unassigned_interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="unassigned@interviewparts.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    unassigned_headers = auth_headers(unassigned_interviewer["access_token"])

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "interviewer_user_ids": [assigned_id]},
        headers=owner_headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text
    interview = schedule_response.json()
    assert interview["interviewer_user_ids"] == [assigned_id]

    assigned_view = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=assigned_headers,
    )
    assert assigned_view.status_code == 200
    assert len(assigned_view.json()) == 1

    unassigned_view = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=unassigned_headers,
    )
    assert unassigned_view.status_code == 200
    assert unassigned_view.json() == []


async def test_org_wide_and_recruiter_see_all_interviews_unscoped(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Owner/TA Admin/Recruiter (anyone with interviews.schedule) keep today's unscoped
    company-wide visibility -- only the narrower Interviewer role is scoped down."""
    owner = await signup(client, email="owner@interviewpartsscope.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@interviewpartsscope.com"
    )

    interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="interviewer@interviewpartsscope.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_id = await _get_user_id(client, headers=auth_headers(interviewer["access_token"]))

    await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "interviewer_user_ids": [interviewer_id]},
        headers=owner_headers,
    )

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@interviewpartsscope.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])

    owner_view = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=owner_headers,
    )
    assert len(owner_view.json()) == 1

    recruiter_view = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=recruiter_headers,
    )
    assert len(recruiter_view.json()) == 1


async def test_scheduling_with_invalid_interviewer_rejected(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@invalidinterviewer.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@invalidinterviewer.com"
    )

    other_company_owner = await signup(client, email="owner@othercompany-interviewer.com")
    other_user_id = await _get_user_id(
        client, headers=auth_headers(other_company_owner["access_token"])
    )

    response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "interviewer_user_ids": [other_user_id]},
        headers=owner_headers,
    )
    assert response.status_code == 400


async def test_updating_interviewer_assignment_replaces_participants(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@reassign-interviewer.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@reassign-interviewer.com"
    )

    first_interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="first@reassign-interviewer.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    first_id = await _get_user_id(client, headers=auth_headers(first_interviewer["access_token"]))

    second_interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="second@reassign-interviewer.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    second_headers = auth_headers(second_interviewer["access_token"])
    second_id = await _get_user_id(client, headers=second_headers)

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={"scheduled_at": _future_iso(), "interviewer_user_ids": [first_id]},
        headers=owner_headers,
    )
    interview_id = schedule_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}/{interview_id}",
        json={"interviewer_user_ids": [second_id]},
        headers=owner_headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["interviewer_user_ids"] == [second_id]

    second_view = await client.get(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        headers=second_headers,
    )
    assert len(second_view.json()) == 1

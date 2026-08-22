import uuid as uuid_module

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


async def test_candidate_send_creates_thread_and_company_can_reply(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@messages-basic.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-basic.com"
    )

    send_response = await client.post(
        f"/api/v1/messages/{application['id']}",
        json={"body": "Hi, just checking in on my application."},
        headers=candidate_headers,
    )
    assert send_response.status_code == 201, send_response.text
    thread = send_response.json()
    assert len(thread["messages"]) == 1
    assert thread["messages"][0]["is_mine"] is True
    assert thread["messages"][0]["sender_type"] == "candidate"

    company_view = await client.get(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}", headers=owner_headers
    )
    assert company_view.status_code == 200, company_view.text
    company_thread = company_view.json()
    assert len(company_thread["messages"]) == 1
    assert company_thread["messages"][0]["is_mine"] is False
    assert company_thread["messages"][0]["sender_label"] == application["callsign"]

    reply_response = await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "Thanks for reaching out -- we'll be in touch this week."},
        headers=owner_headers,
    )
    assert reply_response.status_code == 201, reply_response.text
    reply_thread = reply_response.json()
    assert len(reply_thread["messages"]) == 2
    assert reply_thread["messages"][-1]["is_mine"] is True
    assert reply_thread["messages"][-1]["sender_type"] == "company"


async def test_company_reply_emails_the_candidate(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(
        client, email="owner@messages-notify.com", company_name="Notify Messages Co"
    )
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-notify.com"
    )
    # Candidate's own first message doesn't need to email themselves.
    await client.post(
        f"/api/v1/messages/{application['id']}",
        json={"body": "Hi, just checking in."},
        headers=candidate_headers,
    )
    assert sent_emails.sent == []

    reply_response = await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "Thanks for reaching out."},
        headers=owner_headers,
    )
    assert reply_response.status_code == 201, reply_response.text

    assert len(sent_emails.sent) == 1
    email = sent_emails.sent[0]
    assert email["to"] == "candidate@messages-notify.com"
    assert "Notify Messages Co" in email["subject"]
    assert application["id"] in email["body"]


async def test_unread_counts_and_mark_read_on_open(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@messages-unread.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-unread.com"
    )

    # Company messages first -- candidate's inbox should show 1 unread.
    await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "We'd like to schedule a call."},
        headers=owner_headers,
    )

    threads_response = await client.get("/api/v1/messages", headers=candidate_headers)
    assert threads_response.status_code == 200, threads_response.text
    threads = threads_response.json()
    assert len(threads) == 1
    assert threads[0]["unread_count"] == 1
    assert threads[0]["application_id"] == application["id"]

    # Opening the thread marks it read.
    open_response = await client.get(
        f"/api/v1/messages/{application['id']}", headers=candidate_headers
    )
    assert open_response.status_code == 200, open_response.text

    threads_after = await client.get("/api/v1/messages", headers=candidate_headers)
    assert threads_after.json()[0]["unread_count"] == 0

    # Candidate replies -- company-side applicant list should now show 1 unread.
    await client.post(
        f"/api/v1/messages/{application['id']}",
        json={"body": "Sure, happy to chat."},
        headers=candidate_headers,
    )
    applicants_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert applicants_response.status_code == 200, applicants_response.text
    applicants = applicants_response.json()
    assert len(applicants) == 1
    assert applicants[0]["unread_message_count"] == 1

    # Opening the thread on the company side marks it read too.
    await client.get(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}", headers=owner_headers
    )
    applicants_after = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=owner_headers
    )
    assert applicants_after.json()[0]["unread_message_count"] == 0


async def test_recruiter_can_view_and_send(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    """Recruiter (renamed + permission-expanded from the old Member) now has both messages.view
    and messages.send -- unlike old Member, which was view-only. No other Phase 3 role has any
    messages permission at all, so the "view but not send" boundary this test used to check no
    longer has a real counterpart; test_hiring_manager_has_no_message_access below covers the
    real new floor (zero access) instead."""
    owner = await signup(client, email="owner@messages-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-memberperm.com"
    )
    await client.post(
        f"/api/v1/messages/{application['id']}",
        json={"body": "Hello!"},
        headers=candidate_headers,
    )

    recruiter = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="recruiter@messages-memberperm.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    recruiter_headers = auth_headers(recruiter["access_token"])

    view_response = await client.get(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        headers=recruiter_headers,
    )
    assert view_response.status_code == 200, view_response.text

    send_allowed = await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "Replying as a Recruiter"},
        headers=recruiter_headers,
    )
    assert send_allowed.status_code == 201, send_allowed.text


async def test_hiring_manager_has_no_message_access(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@messages-hmperm.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-hmperm.com"
    )

    hiring_manager = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="hiringmanager@messages-hmperm.com",
        role="Hiring Manager",
        sent_emails=sent_emails,
    )
    hiring_manager_headers = auth_headers(hiring_manager["access_token"])

    view_denied = await client.get(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        headers=hiring_manager_headers,
    )
    assert view_denied.status_code == 403

    send_denied = await client.post(
        f"/api/v1/messages/mine/{job['id']}/applicants/{application['id']}",
        json={"body": "Should fail"},
        headers=hiring_manager_headers,
    )
    assert send_denied.status_code == 403


async def test_cross_tenant_and_cross_candidate_isolation(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner-a@messages-isolation.com")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)
    application_a, candidate_headers_a = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="candidate-a@messages-isolation.com"
    )

    owner_b = await signup(client, email="owner-b@messages-isolation-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    # Company B has no such job/application -- 404, not leaked data.
    cross_tenant_view = await client.get(
        f"/api/v1/messages/mine/{job_a['id']}/applicants/{application_a['id']}", headers=headers_b
    )
    assert cross_tenant_view.status_code == 404

    # Candidate B never applied to this job -- can't read or send on A's application.
    candidate_b_tokens = await candidate_signup(client, email="candidate-b@messages-isolation.com")
    candidate_headers_b = auth_headers(candidate_b_tokens["access_token"])
    cross_candidate_view = await client.get(
        f"/api/v1/messages/{application_a['id']}", headers=candidate_headers_b
    )
    assert cross_candidate_view.status_code == 404
    cross_candidate_send = await client.post(
        f"/api/v1/messages/{application_a['id']}",
        json={"body": "Not my application"},
        headers=candidate_headers_b,
    )
    assert cross_candidate_send.status_code == 404


async def test_burn_project_purges_message_threads_and_messages(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@messages-burn.com", company_name="Burn Messages Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers, title="Role With Messages")
    project_id = project["id"]

    job = await _create_and_publish_job(client, headers=headers, project_id=project_id)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="candidate@messages-burn.com"
    )
    await client.post(
        f"/api/v1/messages/{application['id']}",
        json={"body": "Hello!"},
        headers=candidate_headers,
    )

    assert (
        await _table_row_count(
            "message_threads", "shadow_application_id", application["id"], company_id=company_id
        )
        == 1
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text
    categories = burn_response.json()["certificate"]["data_categories_destroyed"]
    assert "Candidate/company messages" in categories

    assert (
        await _table_row_count(
            "message_threads", "shadow_application_id", application["id"], company_id=company_id
        )
        == 0
    )

import uuid

from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, platform_admin_headers, signup

_BOOTSTRAP_ADMIN_EMAIL = "samuel@stormtalent.co.uk"


async def test_platform_admin_login_and_me(client: AsyncClient) -> None:
    headers = await platform_admin_headers(client)
    me_response = await client.get("/api/v1/platform-admin/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email"] == _BOOTSTRAP_ADMIN_EMAIL


async def test_free_email_domain_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Jamie Recruiter",
            "company_name": "Acme Inc",
            "work_email": "jamie@gmail.com",
            "password": "correct horse battery staple",
        },
    )
    assert response.status_code == 400, response.text
    assert "verified professional organisations" in response.json()["detail"]


async def test_duplicate_pending_request_is_rejected(client: AsyncClient) -> None:
    payload = {
        "full_name": "Jamie Recruiter",
        "company_name": "Duplicate Requests Co",
        "work_email": "jamie@duprequest.com",
        "password": "correct horse battery staple",
    }
    first = await client.post("/api/v1/company-access/requests", json=payload)
    assert first.status_code == 201, first.text

    second = await client.post("/api/v1/company-access/requests", json=payload)
    assert second.status_code == 409, second.text


async def test_existing_workspace_domain_is_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@existingworkspace.com")
    assert owner["access_token"]

    response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Someone Else",
            "company_name": "Existing Workspace Co",
            "work_email": "someone-else@existingworkspace.com",
            "password": "correct horse battery staple",
        },
    )
    assert response.status_code == 409, response.text
    assert "already has a Phantom workspace" in response.json()["detail"]


async def test_non_platform_admin_cannot_access_admin_routes(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@notanadmin.com")
    company_headers = auth_headers(owner["access_token"])

    list_with_company_token = await client.get(
        "/api/v1/company-access/requests", headers=company_headers
    )
    assert list_with_company_token.status_code == 401, list_with_company_token.text

    list_with_no_auth = await client.get("/api/v1/company-access/requests")
    assert list_with_no_auth.status_code == 401, list_with_no_auth.text


async def test_pending_request_appears_in_admin_queue(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    submit_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Quinn Queue",
            "company_name": "Queue Visibility Co",
            "work_email": "quinn@queuevisibility.com",
            "password": "correct horse battery staple",
        },
    )
    assert submit_response.status_code == 201, submit_response.text

    list_response = await client.get("/api/v1/company-access/requests", headers=admin_headers)
    assert list_response.status_code == 200, list_response.text
    emails = [r["work_email"] for r in list_response.json()]
    assert "quinn@queuevisibility.com" in emails


async def test_approving_a_request_creates_a_real_login_capable_account(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    admin_headers = await platform_admin_headers(client)
    password = "correct horse battery staple"
    submit_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Taylor Founder",
            "company_name": "Approve Me Co",
            "work_email": "taylor@approveme.com",
            "password": password,
        },
    )
    assert submit_response.status_code == 201, submit_response.text
    request_id = submit_response.json()["id"]

    login_before_approval = await client.post(
        "/api/v1/auth/login", json={"email": "taylor@approveme.com", "password": password}
    )
    assert login_before_approval.status_code == 401, login_before_approval.text

    approve_response = await client.post(
        f"/api/v1/company-access/requests/{request_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"

    login_after_approval = await client.post(
        "/api/v1/auth/login", json={"email": "taylor@approveme.com", "password": password}
    )
    assert login_after_approval.status_code == 200, login_after_approval.text
    assert login_after_approval.json()["access_token"]

    approved_email = [e for e in sent_emails.sent if e["to"] == "taylor@approveme.com"]
    assert any("ready" in e["subject"].lower() for e in approved_email)


async def test_rejecting_a_request_permanently_blocks_login(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    password = "correct horse battery staple"
    submit_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Rex Rejected",
            "company_name": "Reject Me Co",
            "work_email": "rex@rejectme.com",
            "password": password,
        },
    )
    assert submit_response.status_code == 201, submit_response.text
    request_id = submit_response.json()["id"]

    reject_response = await client.post(
        f"/api/v1/company-access/requests/{request_id}/reject",
        json={"reason": "Could not verify organisation"},
        headers=admin_headers,
    )
    assert reject_response.status_code == 200, reject_response.text
    assert reject_response.json()["status"] == "rejected"

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "rex@rejectme.com", "password": password}
    )
    assert login_response.status_code == 401, login_response.text

    # Rejected -- not reviewable again.
    second_reject = await client.post(
        f"/api/v1/company-access/requests/{request_id}/reject", headers=admin_headers
    )
    assert second_reject.status_code == 409, second_reject.text


async def test_request_info_sends_email_without_changing_status(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    admin_headers = await platform_admin_headers(client)
    submit_response = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Iris Info",
            "company_name": "Info Needed Co",
            "work_email": "iris@infoneeded.com",
            "password": "correct horse battery staple",
        },
    )
    assert submit_response.status_code == 201, submit_response.text
    request_id = submit_response.json()["id"]

    response = await client.post(
        f"/api/v1/company-access/requests/{request_id}/request-info",
        json={"message": "Can you confirm your company registration number?"},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending"

    info_email = [e for e in sent_emails.sent if e["to"] == "iris@infoneeded.com"]
    assert any("more information" in e["subject"].lower() for e in info_email)

    # Still reviewable afterward.
    approve_response = await client.post(
        f"/api/v1/company-access/requests/{request_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200, approve_response.text


async def test_request_queue_is_filterable_by_status(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Filt Er",
            "company_name": "Filter Test Co",
            "work_email": "filter@filtertest.com",
            "password": "correct horse battery staple",
        },
    )

    pending = await client.get(
        "/api/v1/company-access/requests", params={"status": "pending"}, headers=admin_headers
    )
    assert pending.status_code == 200
    assert any(r["work_email"] == "filter@filtertest.com" for r in pending.json())

    approved_only = await client.get(
        "/api/v1/company-access/requests", params={"status": "approved"}, headers=admin_headers
    )
    assert approved_only.status_code == 200
    assert all(r["status"] == "approved" for r in approved_only.json())

    all_requests = await client.get(
        "/api/v1/company-access/requests", params={"status": "all"}, headers=admin_headers
    )
    assert all_requests.status_code == 200
    assert any(r["work_email"] == "filter@filtertest.com" for r in all_requests.json())


async def test_stats_reflect_real_counts(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    await signup(client, email="owner@statscheck.com")

    response = await client.get("/api/v1/company-access/stats", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["active_companies"] >= 1
    assert set(body.keys()) == {
        "pending_requests",
        "approved_requests",
        "rejected_requests",
        "active_companies",
        "suspended_companies",
    }


async def test_suspend_and_reactivate_company(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    owner = await signup(client, email="owner@suspendreactivate.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]

    suspend_response = await client.post(
        f"/api/v1/companies/{company_id}/suspend", headers=admin_headers
    )
    assert suspend_response.status_code == 200, suspend_response.text
    assert suspend_response.json()["status"] == "suspended"

    # Idempotency guard.
    double_suspend = await client.post(
        f"/api/v1/companies/{company_id}/suspend", headers=admin_headers
    )
    assert double_suspend.status_code == 409

    blocked = await client.get("/api/v1/auth/me", headers=headers)
    assert blocked.status_code == 403

    reactivate_response = await client.post(
        f"/api/v1/companies/{company_id}/reactivate", headers=admin_headers
    )
    assert reactivate_response.status_code == 200, reactivate_response.text
    assert reactivate_response.json()["status"] == "approved"

    unblocked = await client.get("/api/v1/auth/me", headers=headers)
    assert unblocked.status_code == 200


async def test_company_directory_lists_companies_with_user_counts(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    await signup(client, email="owner@directorycheck.com")

    response = await client.get("/api/v1/companies", headers=admin_headers)
    assert response.status_code == 200, response.text
    companies = response.json()
    match = next((c for c in companies if c["email_domain"] == "directorycheck.com"), None)
    assert match is not None
    assert match["user_count"] == 1
    assert match["status"] == "approved"


async def test_non_platform_admin_cannot_access_company_directory_or_suspend(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@notanadmin2.com")
    company_headers = auth_headers(owner["access_token"])

    list_response = await client.get("/api/v1/companies", headers=company_headers)
    assert list_response.status_code == 401

    me = await client.get("/api/v1/auth/me", headers=company_headers)
    company_id = me.json()["company_id"]
    suspend_response = await client.post(
        f"/api/v1/companies/{company_id}/suspend", headers=company_headers
    )
    assert suspend_response.status_code == 401


async def test_audit_log_records_every_admin_action_type(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)

    # Approve.
    approve_submit = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Audit Approve",
            "company_name": "Audit Approve Co",
            "work_email": "auditapprove@auditapprovetest.com",
            "password": "correct horse battery staple",
        },
    )
    approve_id = approve_submit.json()["id"]
    await client.post(
        f"/api/v1/company-access/requests/{approve_id}/approve", headers=admin_headers
    )

    # Reject.
    reject_submit = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Audit Reject",
            "company_name": "Audit Reject Co",
            "work_email": "auditreject@auditrejecttest.com",
            "password": "correct horse battery staple",
        },
    )
    reject_id = reject_submit.json()["id"]
    await client.post(f"/api/v1/company-access/requests/{reject_id}/reject", headers=admin_headers)

    # Info requested.
    info_submit = await client.post(
        "/api/v1/company-access/requests",
        json={
            "full_name": "Audit Info",
            "company_name": "Audit Info Co",
            "work_email": "auditinfo@auditinfotest.com",
            "password": "correct horse battery staple",
        },
    )
    info_id = info_submit.json()["id"]
    await client.post(
        f"/api/v1/company-access/requests/{info_id}/request-info",
        json={"message": "Need more detail"},
        headers=admin_headers,
    )

    # Suspend + reactivate.
    owner = await signup(client, email="owner@audittest2.com")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(owner["access_token"]))
    company_id = me.json()["company_id"]
    await client.post(f"/api/v1/companies/{company_id}/suspend", headers=admin_headers)
    await client.post(f"/api/v1/companies/{company_id}/reactivate", headers=admin_headers)

    log_response = await client.get("/api/v1/company-access/audit-log", headers=admin_headers)
    assert log_response.status_code == 200, log_response.text
    actions = {entry["action"] for entry in log_response.json()}
    assert {
        "access_request.approved",
        "access_request.rejected",
        "access_request.info_requested",
        "company.suspended",
        "company.reactivated",
    }.issubset(actions)


async def test_suspended_company_is_blocked_from_the_ats_globally(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@suspendme.com")
    headers = auth_headers(owner["access_token"])

    # Confirm the workspace works before suspension.
    me_before = await client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200, me_before.text

    from app.db.base import auth_session_factory
    from app.modules.companies.repository import CompanyRepository

    async with auth_session_factory() as session:
        company = await CompanyRepository(session).get_by_id(
            uuid.UUID(me_before.json()["company_id"])
        )
        assert company is not None
        company.status = "suspended"
        await session.commit()

    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 403, me_after.text

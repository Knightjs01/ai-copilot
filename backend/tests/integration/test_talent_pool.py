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


async def _create_and_publish_job(client: AsyncClient, *, headers: dict) -> dict:
    response = await client.post("/api/v1/shadow-jobs", json=_JOB_PAYLOAD, headers=headers)
    assert response.status_code == 201, response.text
    job = response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text
    return publish_response.json()


async def _close_job(client: AsyncClient, *, job_id: str, headers: dict) -> dict:
    response = await client.post(f"/api/v1/shadow-jobs/mine/{job_id}/close", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


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


async def _build_and_approve_discoverable_passport(
    client: AsyncClient, *, email: str, full_name: str = "Jamie Candidate"
) -> str:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader.",
        "visibility": "discoverable",
        "personal_info": {"legal_name": full_name},
        "career_entries": [],
    }
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=payload, headers=candidate_headers
    )
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    return candidate_headers


async def test_bulk_request_talent_pool_from_search_results(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(
        client, email="owner@talentpool-bulk.com", company_name="Bulk Talent Pool Co"
    )
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)

    candidate_a_headers = await _build_and_approve_discoverable_passport(
        client, email="candidate-a@talentpool-bulk.com", full_name="Candidate A"
    )
    candidate_b_headers = await _build_and_approve_discoverable_passport(
        client, email="candidate-b@talentpool-bulk.com", full_name="Candidate B"
    )

    search_response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=headers
    )
    assert search_response.status_code == 200, search_response.text
    callsigns = [r["callsign"] for r in search_response.json()]
    assert len(callsigns) == 2

    bulk_response = await client.post(
        "/api/v1/talent-pool/mine/search/request-bulk",
        json={"job_id": job["id"], "callsigns": callsigns, "note": "Strong bench for later"},
        headers=headers,
    )
    assert bulk_response.status_code == 200, bulk_response.text
    body = bulk_response.json()
    assert set(body["requested"]) == set(callsigns)
    assert body["skipped"] == []

    # Both candidates got a real email notification.
    assert len(sent_emails.sent) == 2
    assert {e["to"] for e in sent_emails.sent} == {
        "candidate-a@talentpool-bulk.com",
        "candidate-b@talentpool-bulk.com",
    }
    assert all("Bulk Talent Pool Co" in e["subject"] for e in sent_emails.sent)

    # Each candidate can see the pending request on their own side.
    for candidate_headers in (candidate_a_headers, candidate_b_headers):
        my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
        assert my_requests.status_code == 200
        assert len(my_requests.json()) == 1
        assert my_requests.json()[0]["status"] == "requested"
        assert my_requests.json()[0]["source_role_title"] == job["title"]


async def test_bulk_request_skips_duplicates_and_ineligible_candidates(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@talentpool-bulkskip.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)

    dup_candidate_headers = await _build_and_approve_discoverable_passport(
        client, email="candidate-dup@talentpool-bulkskip.com", full_name="Candidate Dup"
    )
    private_candidate_headers = await _build_and_approve_discoverable_passport(
        client, email="candidate-private@talentpool-bulkskip.com", full_name="Candidate Private"
    )

    # Resolve each candidate's own callsign directly rather than assuming search-result order
    # matches creation order -- the two are unrelated and must not be conflated.
    dup_me = await client.get("/api/v1/phantom-passport/me", headers=dup_candidate_headers)
    dup_callsign = dup_me.json()["callsign"]
    private_me = await client.get("/api/v1/phantom-passport/me", headers=private_candidate_headers)
    private_callsign = private_me.json()["callsign"]

    search_response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=headers
    )
    results = {r["callsign"]: r for r in search_response.json()}
    assert set(results.keys()) == {dup_callsign, private_callsign}

    # First bulk call succeeds for the "dup" candidate, establishing an active grant.
    first_response = await client.post(
        "/api/v1/talent-pool/mine/search/request-bulk",
        json={"job_id": job["id"], "callsigns": [dup_callsign]},
        headers=headers,
    )
    assert first_response.status_code == 200, first_response.text
    assert first_response.json()["requested"] == [dup_callsign]

    # Candidate goes private after being found in search but before the bulk-save fires. PUT
    # replaces the whole passport, so the full payload is resent with visibility flipped.
    await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Senior Product Leader",
            "summary": "A senior product leader.",
            "visibility": "private",
            "personal_info": {"legal_name": "Candidate Private"},
            "career_entries": [],
        },
        headers=private_candidate_headers,
    )

    second_response = await client.post(
        "/api/v1/talent-pool/mine/search/request-bulk",
        json={"job_id": job["id"], "callsigns": [dup_callsign, private_callsign]},
        headers=headers,
    )
    assert second_response.status_code == 200, second_response.text
    body = second_response.json()
    assert body["requested"] == []
    skipped_by_callsign = {s["callsign"]: s["reason"] for s in body["skipped"]}
    assert skipped_by_callsign[dup_callsign] == "Already requested or granted"
    assert skipped_by_callsign[private_callsign] == "No longer discoverable"


async def test_request_talent_pool_requires_eligible_state(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpool-eligible.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-eligible.com"
    )

    # Still submitted/under_review and the job is still published — not eligible yet.
    premature = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert premature.status_code == 400

    await _close_job(client, job_id=job["id"], headers=headers)

    request_response = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={"note": "Great designer, keep in mind for future roles"},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text
    body = request_response.json()
    assert body["status"] == "requested"
    assert body["source_role_title"] == job["title"]
    assert body["callsign"] is None


async def test_duplicate_talent_pool_request_rejected_then_allowed_after_decline(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@talentpool-dup.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-dup.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)

    first = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert second.status_code == 409

    my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
    grant_id = my_requests.json()[0]["id"]
    decline_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )
    assert decline_response.status_code == 200, decline_response.text

    # After a decline, a fresh request cycle is allowed for the same (candidate, company) pair.
    third = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert third.status_code == 201, third.text


async def test_candidate_can_view_and_grant_talent_pool_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpool-grant.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-grant.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)
    await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={"note": "Would love to keep in touch"},
        headers=headers,
    )

    my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
    assert my_requests.status_code == 200, my_requests.text
    pending = my_requests.json()[0]
    assert pending["status"] == "requested"
    assert pending["note"] == "Would love to keep in touch"
    assert pending["source_role_title"] == job["title"]

    # Company can't see this candidate in its Talent Pool yet -- only requested, not granted.
    before_grant = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert before_grant.json() == []

    grant_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{pending['id']}/respond",
        json={"approve": True, "scope": "company_wide"},
        headers=candidate_headers,
    )
    assert grant_response.status_code == 200, grant_response.text
    granted = grant_response.json()
    assert granted["status"] == "granted"
    assert granted["scope"] == "company_wide"
    assert granted["review_date"] is not None

    # The Talent Pool surfaces the candidate's stable, persistent Passport callsign -- not the
    # fresh per-application Shadow callsign (application["callsign"]), which is deliberately
    # different by design (unlinkable across applications). Confirm it's the candidate's real,
    # persistent identity by cross-checking against their own Passport.
    my_passport = await client.get("/api/v1/phantom-passport/me", headers=candidate_headers)
    assert my_passport.status_code == 200, my_passport.text
    persistent_callsign = my_passport.json()["callsign"]
    assert persistent_callsign is not None
    assert persistent_callsign != application["callsign"]

    pool = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert pool.status_code == 200, pool.text
    pool_items = pool.json()
    assert len(pool_items) == 1
    assert pool_items[0]["callsign"] == persistent_callsign
    assert pool_items[0]["scope"] == "company_wide"
    assert pool_items[0]["source_role_title"] == job["title"]


async def test_candidate_can_decline_talent_pool_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpool-decline.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-decline.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)
    await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
    grant_id = my_requests.json()[0]["id"]

    decline_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )
    assert decline_response.status_code == 200, decline_response.text
    assert decline_response.json()["status"] == "declined"

    pool = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert pool.json() == []

    # Responding twice is rejected -- the decision is final for this cycle.
    second_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert second_response.status_code == 400


async def test_withdraw_talent_pool_grant(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpool-withdraw.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-withdraw.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)
    await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
    grant_id = my_requests.json()[0]["id"]
    await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )

    pool_before = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert len(pool_before.json()) == 1

    withdraw_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/withdraw", headers=candidate_headers
    )
    assert withdraw_response.status_code == 200, withdraw_response.text
    assert withdraw_response.json()["status"] == "withdrawn"

    pool_after = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert pool_after.json() == []

    # A fresh request cycle is possible again after a withdrawal.
    fresh_request = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert fresh_request.status_code == 201, fresh_request.text

    # Withdrawing something that isn't currently granted is rejected.
    second_withdraw = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/withdraw", headers=candidate_headers
    )
    assert second_withdraw.status_code == 400


async def test_talent_pool_request_scoped_to_owning_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpool-scope.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _owner_candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-scope.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)
    await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    my_requests = await client.get(
        "/api/v1/talent-pool/my-requests", headers=_owner_candidate_headers
    )
    grant_id = my_requests.json()[0]["id"]

    other_tokens = await candidate_signup(client, email="other@talentpool-scope.com")
    other_headers = auth_headers(other_tokens["access_token"])

    response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True},
        headers=other_headers,
    )
    assert response.status_code == 404

    other_requests = await client.get("/api/v1/talent-pool/my-requests", headers=other_headers)
    assert other_requests.json() == []


async def test_talent_pool_isolated_per_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@talentpool-tenant-a.com", company_name="Tenant A")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)
    application_a, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="applicant@talentpool-tenant-a.com"
    )
    await _close_job(client, job_id=job_a["id"], headers=headers_a)
    await client.post(
        f"/api/v1/talent-pool/mine/{job_a['id']}/applicants/{application_a['id']}/request",
        json={},
        headers=headers_a,
    )
    my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
    grant_id = my_requests.json()[0]["id"]
    await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )

    owner_b = await signup(client, email="owner@talentpool-tenant-b.com", company_name="Tenant B")
    headers_b = auth_headers(owner_b["access_token"])
    pool_b = await client.get("/api/v1/talent-pool/mine", headers=headers_b)
    assert pool_b.status_code == 200, pool_b.text
    assert pool_b.json() == []


async def test_talent_pool_request_requires_permission(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@talentpool-perms.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@talentpool-perms.com"
    )
    await _close_job(client, job_id=job["id"], headers=headers)

    interviewer = await invite_and_accept(
        client,
        inviter_headers=headers,
        email="interviewer@talentpool-perms.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_headers = auth_headers(interviewer["access_token"])

    response = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=interviewer_headers,
    )
    assert response.status_code == 403

    view_response = await client.get("/api/v1/talent-pool/mine", headers=interviewer_headers)
    assert view_response.status_code == 403


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


async def test_project_burn_nulls_source_application_without_deleting_grant(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@talentpool-burn.com", company_name="Burn Talent Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["company_id"]
    project = await create_project(client, headers=headers, title="Role With Talent Pool Grant")
    project_id = project["id"]

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own our core platform.",
            "description": "Full role description.",
            "project_id": project_id,
        },
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    await client.post(f"/api/v1/shadow-jobs/mine/{job_id}/publish", headers=headers)

    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job_id, email="applicant@talentpool-burn.com"
    )
    await _close_job(client, job_id=job_id, headers=headers)

    request_response = await client.post(
        f"/api/v1/talent-pool/mine/{job_id}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text
    grant_id = request_response.json()["id"]

    await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project_id}/burn",
        headers=await step_up_headers(client, headers=headers),
    )
    assert burn_response.status_code == 200, burn_response.text

    # The grant row survives the project burn -- it's scoped to (candidate, company), not the
    # project. Its source application FK goes null (ON DELETE SET NULL); source_role_title is a
    # denormalized snapshot so the human-readable context survives regardless.
    assert await _table_row_count("talent_pool_grants", "id", grant_id, company_id=company_id) == 1
    still_in_pool = await client.get("/api/v1/talent-pool/mine", headers=headers)
    assert still_in_pool.status_code == 200, still_in_pool.text
    assert len(still_in_pool.json()) == 1
    assert still_in_pool.json()[0]["source_role_title"] == "Staff Engineer"


async def test_list_eligible_for_project_scopes_by_company_wide_and_project_only(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@talentpool-eligible-project.com")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers, title="Eligible Project")
    other_project = await create_project(client, headers=headers, title="Other Project")

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={**_JOB_PAYLOAD, "project_id": project["id"]},
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text

    company_wide_headers = await _build_and_approve_discoverable_passport(
        client, email="candidate-wide@talentpool-eligible-project.com", full_name="Wide Candidate"
    )
    project_only_headers = await _build_and_approve_discoverable_passport(
        client,
        email="candidate-narrow@talentpool-eligible-project.com",
        full_name="Narrow Candidate",
    )
    company_wide_me = await client.get("/api/v1/phantom-passport/me", headers=company_wide_headers)
    company_wide_callsign = company_wide_me.json()["callsign"]
    project_only_me = await client.get("/api/v1/phantom-passport/me", headers=project_only_headers)
    project_only_callsign = project_only_me.json()["callsign"]

    bulk_response = await client.post(
        "/api/v1/talent-pool/mine/search/request-bulk",
        json={"job_id": job["id"], "callsigns": [company_wide_callsign, project_only_callsign]},
        headers=headers,
    )
    assert bulk_response.status_code == 200, bulk_response.text

    for candidate_headers, scope in (
        (company_wide_headers, "company_wide"),
        (project_only_headers, "project_only"),
    ):
        my_requests = await client.get("/api/v1/talent-pool/my-requests", headers=candidate_headers)
        grant_id = my_requests.json()[0]["id"]
        respond = await client.post(
            f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
            json={"approve": True, "scope": scope},
            headers=candidate_headers,
        )
        assert respond.status_code == 200, respond.text

    # Eligible for the linked project: both (company_wide is always eligible, project_only
    # matches this exact project).
    eligible_for_project = await client.get(
        f"/api/v1/talent-pool/mine/projects/{project['id']}/eligible", headers=headers
    )
    assert eligible_for_project.status_code == 200, eligible_for_project.text
    eligible_callsigns = {c["callsign"] for c in eligible_for_project.json()}
    assert eligible_callsigns == {company_wide_callsign, project_only_callsign}

    # Eligible for a different project: only the company_wide grant.
    eligible_for_other = await client.get(
        f"/api/v1/talent-pool/mine/projects/{other_project['id']}/eligible", headers=headers
    )
    assert eligible_for_other.status_code == 200, eligible_for_other.text
    other_callsigns = {c["callsign"] for c in eligible_for_other.json()}
    assert other_callsigns == {company_wide_callsign}


async def test_list_eligible_for_project_404s_for_wrong_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner-a@talentpool-eligible-404.com")
    headers_a = auth_headers(owner_a["access_token"])
    project_a = await create_project(client, headers=headers_a, title="Project A")

    owner_b = await signup(client, email="owner-b@talentpool-eligible-404-b.com")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get(
        f"/api/v1/talent-pool/mine/projects/{project_a['id']}/eligible", headers=headers_b
    )
    assert response.status_code == 404

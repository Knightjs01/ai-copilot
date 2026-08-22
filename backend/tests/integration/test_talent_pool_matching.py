from httpx import AsyncClient

from tests.conftest import CapturingEmailSender, FakePassportMatchingLLMClient
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


async def _grant_talent_pool(
    client: AsyncClient,
    *,
    owner_headers: dict,
    email: str,
    scope: str,
    project_id: str | None = None,
) -> dict:
    """End-to-end: publish a source job (optionally linked to a project), apply, close the job,
    request Talent Pool, and grant with the given scope -- the exact real lifecycle a grant with
    a real source_project_id goes through. Returns the source job, since ShadowJob.project_id is
    hard-unique (a project can have at most one Shadow Job ever) -- callers testing project_only
    eligibility must re-search THIS job, not create a second one on the same project."""
    job = await _create_and_publish_job(client, headers=owner_headers, project_id=project_id)
    tokens = await candidate_signup(client, email=email, full_name="Talent Pool Candidate")
    candidate_headers = auth_headers(tokens["access_token"])
    save_response = await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Senior Product Designer",
            "summary": "A senior product designer.",
            "personal_info": {"legal_name": "Talent Pool Candidate"},
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
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    application = apply_response.json()

    close_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/close", headers=owner_headers
    )
    assert close_response.status_code == 200, close_response.text

    request_response = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=owner_headers,
    )
    assert request_response.status_code == 201, request_response.text
    grant_id = request_response.json()["id"]

    respond_response = await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": True, "scope": scope},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text
    return job


async def test_company_wide_grant_matches_any_new_job_at_company(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-companywide.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-companywide.com",
        scope="company_wide",
    )

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    response = await client.get(
        f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert len(results) == 1
    assert results[0]["match_tier"] == "Strong Match"
    assert results[0]["scope"] == "company_wide"
    assert results[0]["source_role_title"] == _JOB_PAYLOAD["title"]


async def test_project_only_grant_matches_only_the_same_project(client: AsyncClient) -> None:
    """ShadowJob.project_id is hard-unique -- a project can have at most one Shadow Job ever, so
    project_only can never match a genuinely different, new job "in the same project" (no second
    job can exist there). What it CAN do is match when the recruiter re-searches the exact
    original job -- e.g. after reopening/republishing a closed role via the same publish endpoint
    (publish_job has no status guard, confirmed in shadow_jobs/service.py)."""
    owner = await signup(client, email="owner@talentpoolmatch-projectonly.com")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers, title="Design Team")
    source_job = await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-projectonly.com",
        scope="project_only",
        project_id=project["id"],
    )

    # Re-searching the exact source job (reopened) -> eligible.
    reopen_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{source_job['id']}/publish", headers=owner_headers
    )
    assert reopen_response.status_code == 200, reopen_response.text
    same_job_response = await client.get(
        f"/api/v1/matches/mine/{source_job['id']}/talent-pool", headers=owner_headers
    )
    assert same_job_response.status_code == 200, same_job_response.text
    assert len(same_job_response.json()) == 1

    # A different project -> not eligible.
    other_project = await create_project(client, headers=owner_headers, title="Engineering Team")
    other_project_job = await _create_and_publish_job(
        client, headers=owner_headers, project_id=other_project["id"]
    )
    other_project_response = await client.get(
        f"/api/v1/matches/mine/{other_project_job['id']}/talent-pool", headers=owner_headers
    )
    assert other_project_response.status_code == 200, other_project_response.text
    assert other_project_response.json() == []

    # No project at all -> not eligible.
    unlinked_job = await _create_and_publish_job(client, headers=owner_headers)
    unlinked_response = await client.get(
        f"/api/v1/matches/mine/{unlinked_job['id']}/talent-pool", headers=owner_headers
    )
    assert unlinked_response.status_code == 200, unlinked_response.text
    assert unlinked_response.json() == []


async def test_project_only_grant_stops_matching_after_source_project_is_burned(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-burn.com")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers, title="Burned Project")
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-burn.com",
        scope="project_only",
        project_id=project["id"],
    )

    burn_response = await client.post(
        f"/api/v1/projects/{project['id']}/burn",
        headers=await step_up_headers(client, headers=owner_headers),
    )
    assert burn_response.status_code == 200, burn_response.text

    # Even a brand-new job cannot match -- source_project_id is now null, which can never equal
    # any real project id.
    other_project = await create_project(client, headers=owner_headers, title="New Project")
    new_job = await _create_and_publish_job(
        client, headers=owner_headers, project_id=other_project["id"]
    )
    response = await client.get(
        f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_only_granted_status_is_eligible_for_matching(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-status.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)

    tokens = await candidate_signup(
        client, email="declined@talentpoolmatch-status.com", full_name="Declined Candidate"
    )
    candidate_headers = auth_headers(tokens["access_token"])
    await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Product Designer",
            "personal_info": {"legal_name": "Declined Candidate"},
            "career_entries": [],
        },
        headers=candidate_headers,
    )
    await client.post("/api/v1/phantom-passport/me/approve", headers=candidate_headers)
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    application = apply_response.json()
    await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/close", headers=owner_headers)

    request_response = await client.post(
        f"/api/v1/talent-pool/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=owner_headers,
    )
    grant_id = request_response.json()["id"]
    # Declined, not granted -- must never appear in matches for any job.
    await client.post(
        f"/api/v1/talent-pool/requests/me/{grant_id}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    response = await client.get(
        f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_talent_pool_matching_isolated_per_company(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner@talentpoolmatch-tenant-a.com", company_name="A")
    headers_a = auth_headers(owner_a["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=headers_a,
        email="candidate@talentpoolmatch-tenant-a.com",
        scope="company_wide",
    )

    owner_b = await signup(client, email="owner@talentpoolmatch-tenant-b.com", company_name="B")
    headers_b = auth_headers(owner_b["access_token"])
    job_b = await _create_and_publish_job(client, headers=headers_b)

    response = await client.get(
        f"/api/v1/matches/mine/{job_b['id']}/talent-pool", headers=headers_b
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_talent_pool_matching_requires_view_permission(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-perms.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)

    interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="interviewer@talentpoolmatch-perms.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_headers = auth_headers(interviewer["access_token"])

    response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/talent-pool", headers=interviewer_headers
    )
    assert response.status_code == 403


async def test_talent_pool_match_enriches_job_facts_with_linked_project_blueprint(
    client: AsyncClient,
    fake_passport_matching_llm_client: FakePassportMatchingLLMClient,
    fake_hiring_blueprint_llm_client,
) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-blueprint.com")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers, title="Staff Designer Team")
    source_job = await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-blueprint.com",
        scope="project_only",
        project_id=project["id"],
    )

    patch_response = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"role_brief": "Looking for a staff product designer."},
        headers=owner_headers,
    )
    assert patch_response.status_code == 200, patch_response.text
    blueprint_response = await client.post(
        f"/api/v1/projects/{project['id']}/hiring-blueprint", headers=owner_headers
    )
    assert blueprint_response.status_code == 200, blueprint_response.text
    alignment_response = await client.put(
        f"/api/v1/projects/{project['id']}/hiring-manager-alignment",
        json={"top_requirements": ["Portfolio of shipped 0-to-1 products"]},
        headers=owner_headers,
    )
    assert alignment_response.status_code == 200, alignment_response.text

    # ShadowJob.project_id is hard-unique -- re-search the same source job (reopened) rather than
    # trying to create a second job on the same project, which the schema doesn't allow.
    reopen_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{source_job['id']}/publish", headers=owner_headers
    )
    assert reopen_response.status_code == 200, reopen_response.text
    response = await client.get(
        f"/api/v1/matches/mine/{source_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    assert len(fake_passport_matching_llm_client.score_calls) == 1
    _, job_facts = fake_passport_matching_llm_client.score_calls[0]
    assert job_facts["role_summary"] == "A fake but deterministic role summary for testing."
    assert job_facts["must_have_qualifications"] == ["Fake required skill"]
    assert job_facts["top_requirements"] == ["Portfolio of shipped 0-to-1 products"]


# --- Phase 3: candidate opportunity workflow --------------------------------------------------


async def test_fresh_match_sends_exactly_one_notification_email(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-notify.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-notify.com",
        scope="company_wide",
    )
    sent_emails.sent.clear()

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    response = await client.get(
        f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    matching_sends = [
        e for e in sent_emails.sent if e["to"] == "candidate@talentpoolmatch-notify.com"
    ]
    assert len(matching_sends) == 1, sent_emails.sent
    assert new_job["id"] in matching_sends[0]["body"]


async def test_repeated_search_does_not_resend_notification(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-noresend.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-noresend.com",
        scope="company_wide",
    )
    sent_emails.sent.clear()

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)

    matching_sends = [
        e for e in sent_emails.sent if e["to"] == "candidate@talentpoolmatch-noresend.com"
    ]
    assert len(matching_sends) == 1, sent_emails.sent


async def test_weak_match_never_sends_email_but_still_appears_in_results(
    client: AsyncClient,
    sent_emails: CapturingEmailSender,
    fake_passport_matching_llm_client: FakePassportMatchingLLMClient,
) -> None:
    from app.modules.passport_matching.llm_client import PassportMatchDraft

    async def _weak_score(*, passport_snapshot: dict, job_facts: dict) -> PassportMatchDraft:
        return PassportMatchDraft(
            match_tier="Weak Match",
            match_score=15,
            strengths=[],
            gaps=["No relevant overlap"],
            summary="A weak fit.",
        )

    fake_passport_matching_llm_client.score_match = _weak_score  # type: ignore[method-assign]

    owner = await signup(client, email="owner@talentpoolmatch-weak.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-weak.com",
        scope="company_wide",
    )
    sent_emails.sent.clear()

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    response = await client.get(
        f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert len(results) == 1
    assert results[0]["match_tier"] == "Weak Match"

    matching_sends = [
        e for e in sent_emails.sent if e["to"] == "candidate@talentpoolmatch-weak.com"
    ]
    assert matching_sends == []


async def test_candidate_can_view_talent_pool_opportunities(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-opportunities.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-opportunities.com",
        scope="company_wide",
    )

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)

    candidate_login = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate@talentpoolmatch-opportunities.com",
            "password": "correct horse battery staple",
        },
    )
    assert candidate_login.status_code == 200, candidate_login.text
    candidate_headers = auth_headers(candidate_login.json()["access_token"])

    opportunities = await client.get(
        "/api/v1/matches/my-talent-pool-opportunities", headers=candidate_headers
    )
    assert opportunities.status_code == 200, opportunities.text
    items = opportunities.json()
    assert len(items) == 1
    assert items[0]["job_id"] == new_job["id"]
    assert items[0]["job_title"] == new_job["title"]
    assert items[0]["match_tier"] == "Strong Match"


async def test_opportunity_hidden_once_job_closed(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-closed.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-closed.com",
        scope="company_wide",
    )

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)
    await client.post(f"/api/v1/shadow-jobs/mine/{new_job['id']}/close", headers=owner_headers)

    candidate_login = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate@talentpoolmatch-closed.com",
            "password": "correct horse battery staple",
        },
    )
    candidate_headers = auth_headers(candidate_login.json()["access_token"])

    opportunities = await client.get(
        "/api/v1/matches/my-talent-pool-opportunities", headers=candidate_headers
    )
    assert opportunities.status_code == 200, opportunities.text
    assert opportunities.json() == []


async def test_opportunity_hidden_once_candidate_already_applied(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-applied.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-applied.com",
        scope="company_wide",
    )

    new_job = await _create_and_publish_job(client, headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)

    candidate_login = await client.post(
        "/api/v1/candidate-auth/login",
        json={
            "email": "candidate@talentpoolmatch-applied.com",
            "password": "correct horse battery staple",
        },
    )
    candidate_headers = auth_headers(candidate_login.json()["access_token"])

    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{new_job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text

    opportunities = await client.get(
        "/api/v1/matches/my-talent-pool-opportunities", headers=candidate_headers
    )
    assert opportunities.status_code == 200, opportunities.text
    assert opportunities.json() == []


async def test_talent_pool_opportunities_isolated_per_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@talentpoolmatch-isolation.com")
    owner_headers = auth_headers(owner["access_token"])
    await _grant_talent_pool(
        client,
        owner_headers=owner_headers,
        email="candidate@talentpoolmatch-isolation.com",
        scope="company_wide",
    )
    new_job = await _create_and_publish_job(client, headers=owner_headers)
    await client.get(f"/api/v1/matches/mine/{new_job['id']}/talent-pool", headers=owner_headers)

    other_tokens = await candidate_signup(client, email="bystander@talentpoolmatch-isolation.com")
    other_headers = auth_headers(other_tokens["access_token"])
    await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Bystander Candidate",
            "personal_info": {"legal_name": "Bystander Candidate"},
            "career_entries": [],
        },
        headers=other_headers,
    )
    await client.post("/api/v1/phantom-passport/me/approve", headers=other_headers)

    opportunities = await client.get(
        "/api/v1/matches/my-talent-pool-opportunities", headers=other_headers
    )
    assert opportunities.status_code == 200, opportunities.text
    assert opportunities.json() == []

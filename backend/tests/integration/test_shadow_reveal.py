from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, signup, step_up_headers

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


async def _apply_with_new_candidate(
    client: AsyncClient, *, job_id: str, email: str, full_name: str = "Jamie Candidate"
) -> tuple[dict, dict]:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    passport_payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader.",
        "career_intent": "actively_looking",
        "personal_info": {"legal_name": full_name, "phone": "+44 20 7946 0958"},
        "career_entries": [
            {
                "title": "VP Product",
                "company_name": "Stripe",
                "company_name_anonymized": "Global Payments Platform",
                "is_current": True,
            }
        ],
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


async def test_request_reveal_transitions_application_status(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-request.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-request.com"
    )

    request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Moving to final interview"},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text
    body = request_response.json()
    assert body["status"] == "pending"
    assert body["callsign"] == application["callsign"]

    applications_response = await client.get(
        "/api/v1/shadow-jobs/applications/me", headers=_candidate_headers
    )
    assert applications_response.json()[0]["status"] == "reveal_requested"


async def test_request_reveal_emails_the_candidate(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(
        client, email="owner@shadowreveal-notify.com", company_name="Notify Reveal Co"
    )
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-notify.com"
    )

    request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Moving to final interview"},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text

    assert len(sent_emails.sent) == 1
    email = sent_emails.sent[0]
    assert email["to"] == "applicant@shadowreveal-notify.com"
    assert "Notify Reveal Co" in email["subject"]
    assert application["id"] in email["body"]


async def test_duplicate_reveal_request_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-dup.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _ = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-dup.com"
    )

    first = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    assert second.status_code == 409


async def test_candidate_can_view_and_approve_reveal_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-approve.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-approve.com",
        full_name="Secret Applicant",
    )

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Ready to move forward"},
        headers=headers,
    )

    pending_view = await client.get(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}", headers=candidate_headers
    )
    assert pending_view.status_code == 200, pending_view.text
    assert pending_view.json()["status"] == "pending"
    assert pending_view.json()["reason"] == "Ready to move forward"

    # Company cannot see the identity before the candidate approves.
    premature_view = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert premature_view.status_code == 400

    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert revealed_response.status_code == 200, revealed_response.text
    revealed = revealed_response.json()
    assert revealed["full_name"] == "Secret Applicant"
    assert revealed["email"] == "applicant@shadowreveal-approve.com"
    assert revealed["career_entries"][0]["company_name"] == "Stripe"

    application_status = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert application_status.json()[0]["status"] == "revealed"


async def test_candidate_can_decline_reveal_request(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-decline.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-decline.com"
    )

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    decline_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )
    assert decline_response.status_code == 200, decline_response.text
    assert decline_response.json()["status"] == "declined"

    still_hidden = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert still_hidden.status_code == 400

    # Responding twice is rejected — the decision is final.
    second_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert second_response.status_code == 400


async def test_respond_with_custom_fields_narrows_disclosure(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-customfields.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-customfields.com",
        full_name="Narrowed Applicant",
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Confirming interest"},
        headers=headers,
    )

    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True, "disclosed_fields": ["full_name"]},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert revealed_response.status_code == 200, revealed_response.text
    revealed = revealed_response.json()
    assert revealed["full_name"] == "Narrowed Applicant"
    assert revealed["email"] is None
    assert revealed["career_entries"] == []
    assert revealed["disclosure_level"] == "custom"
    assert revealed["disclosed_fields"] == ["full_name"]


async def test_respond_with_empty_disclosed_fields_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-emptyfields.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-emptyfields.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True, "disclosed_fields": []},
        headers=candidate_headers,
    )
    assert response.status_code == 400, response.text


async def test_respond_without_disclosed_fields_falls_back_to_tier(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-tierfallback.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-tierfallback.com",
        full_name="Tier Fallback Applicant",
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True, "disclosure_level": "contact"},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert revealed_response.status_code == 200, revealed_response.text
    revealed = revealed_response.json()
    assert revealed["full_name"] == "Tier Fallback Applicant"
    assert revealed["email"] == "applicant@shadowreveal-tierfallback.com"
    assert revealed["phone"] == "+44 20 7946 0958"
    assert revealed["career_entries"] == []
    assert revealed["disclosure_level"] == "contact"
    assert sorted(revealed["disclosed_fields"]) == ["email", "full_name", "phone"]


async def test_reveal_request_scoped_to_owning_candidate(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-scope.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, _owner_candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-scope.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )

    other_tokens = await candidate_signup(client, email="other@shadowreveal-scope.com")
    other_headers = auth_headers(other_tokens["access_token"])

    response = await client.get(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}", headers=other_headers
    )
    assert response.status_code == 404


async def test_my_history_spans_every_application_and_is_isolated_per_candidate(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@shadowreveal-history.com")
    headers = auth_headers(owner["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers)
    job_b = await _create_and_publish_job(client, headers=headers)

    application_a, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job_a["id"], email="applicant@shadowreveal-history.com"
    )
    apply_b = await client.post(
        f"/api/v1/shadow-jobs/board/{job_b['id']}/apply", headers=candidate_headers
    )
    assert apply_b.status_code == 201, apply_b.text
    application_b = apply_b.json()

    # No history yet -- nothing requested.
    empty_history = await client.get("/api/v1/shadow-reveal/my-history", headers=candidate_headers)
    assert empty_history.status_code == 200, empty_history.text
    assert empty_history.json() == []

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job_a['id']}/applicants/{application_a['id']}/request",
        json={"reason": "Ready to move forward"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job_b['id']}/applicants/{application_b['id']}/request",
        json={"reason": "Client submission"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application_a['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application_b['id']}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )

    history = await client.get("/api/v1/shadow-reveal/my-history", headers=candidate_headers)
    assert history.status_code == 200, history.text
    items = history.json()
    assert len(items) == 2
    by_application = {item["shadow_application_id"]: item for item in items}

    approved_item = by_application[application_a["id"]]
    assert approved_item["status"] == "approved"
    assert approved_item["reason"] == "Ready to move forward"
    assert approved_item["responded_at"] is not None
    # Approving at the default (full) level stores the level but leaves disclosed_fields null --
    # that field is only populated when the candidate explicitly narrows disclosure.
    assert approved_item["disclosure_level"] == "full"
    assert approved_item["disclosed_fields"] is None

    declined_item = by_application[application_b["id"]]
    assert declined_item["status"] == "declined"
    assert declined_item["disclosure_level"] is None
    assert declined_item["disclosed_fields"] is None

    # A different candidate's history is completely empty -- no cross-candidate leakage.
    other_tokens = await candidate_signup(client, email="bystander@shadowreveal-history.com")
    other_history = await client.get(
        "/api/v1/shadow-reveal/my-history", headers=auth_headers(other_tokens["access_token"])
    )
    assert other_history.json() == []


async def test_reveal_approval_emails_the_requester(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@shadowreveal-response-notify.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-response-notify.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    sent_emails.sent.clear()  # drop the request-made email, only the response email matters here

    respond_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text

    assert len(sent_emails.sent) == 1
    email = sent_emails.sent[0]
    assert email["to"] == "owner@shadowreveal-response-notify.com"
    assert application["callsign"] in email["subject"]
    assert "approved" in email["subject"]


async def test_reveal_decline_emails_the_requester(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@shadowreveal-decline-notify.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-decline-notify.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    sent_emails.sent.clear()

    respond_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": False},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text

    assert len(sent_emails.sent) == 1
    email = sent_emails.sent[0]
    assert email["to"] == "owner@shadowreveal-decline-notify.com"
    assert "declined" in email["subject"]


async def test_reveal_response_is_unseen_until_applicant_card_is_opened(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@shadowreveal-unseen.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-unseen.com"
    )
    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={},
        headers=headers,
    )
    # Mark the application itself viewed first, so only the reveal-response flag is under test.
    await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/mark-viewed",
        headers=headers,
    )

    await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )

    unseen = await client.get(f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers)
    assert unseen.status_code == 200, unseen.text
    assert unseen.json()[0]["reveal_response_is_new"] is True

    mark_viewed = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/mark-viewed",
        headers=headers,
    )
    assert mark_viewed.status_code == 200, mark_viewed.text
    assert mark_viewed.json()["reveal_response_is_new"] is False

    seen_again = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert seen_again.json()[0]["reveal_response_is_new"] is False


async def _request_and_approve_reveal(
    client: AsyncClient,
    *,
    job_id: str,
    application_id: str,
    headers: dict,
    candidate_headers: dict,
    disclosure_level: str = "full",
) -> None:
    request_response = await client.post(
        f"/api/v1/shadow-reveal/mine/{job_id}/applicants/{application_id}/request",
        json={"reason": "Ready to move forward"},
        headers=headers,
    )
    assert request_response.status_code == 201, request_response.text
    respond_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application_id}/respond",
        json={"approve": True, "disclosure_level": disclosure_level},
        headers=candidate_headers,
    )
    assert respond_response.status_code == 200, respond_response.text


async def test_first_reveal_persists_identity_onto_the_application(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-persist.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-persist.com",
        full_name="Persisted Applicant",
    )
    await _request_and_approve_reveal(
        client,
        job_id=job["id"],
        application_id=application["id"],
        headers=headers,
        candidate_headers=candidate_headers,
    )

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert revealed_response.status_code == 200, revealed_response.text
    assert revealed_response.json()["full_name"] == "Persisted Applicant"

    # The persisted fields must now be readable straight off the applicant list -- no repeated
    # step-up, no repeated decrypt.
    applicants = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    assert applicants.status_code == 200, applicants.text
    profile = applicants.json()[0]
    assert profile["revealed_full_name"] == "Persisted Applicant"
    assert profile["revealed_email"] == "applicant@shadowreveal-persist.com"
    assert profile["revealed_phone"] == "+44 20 7946 0958"

    activity_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/activity",
        headers=headers,
    )
    assert activity_response.status_code == 200, activity_response.text
    actions = [entry["action"] for entry in activity_response.json()]
    assert actions.count("shadow_reveal.identity_viewed") == 1


async def test_second_reveal_view_does_not_re_persist_or_re_log(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-idempotent.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email="applicant@shadowreveal-idempotent.com"
    )
    await _request_and_approve_reveal(
        client,
        job_id=job["id"],
        application_id=application["id"],
        headers=headers,
        candidate_headers=candidate_headers,
    )

    step_up = await step_up_headers(client, headers=headers)
    first = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}", headers=step_up
    )
    assert first.status_code == 200, first.text

    second = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert second.status_code == 200, second.text
    assert second.json()["full_name"] == first.json()["full_name"]

    activity_response = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants/{application['id']}/activity",
        headers=headers,
    )
    actions = [entry["action"] for entry in activity_response.json()]
    assert actions.count("shadow_reveal.identity_viewed") == 1


async def test_basic_disclosure_only_persists_name(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@shadowreveal-persist-basic.com")
    headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client,
        job_id=job["id"],
        email="applicant@shadowreveal-persist-basic.com",
        full_name="Basic Applicant",
    )
    await _request_and_approve_reveal(
        client,
        job_id=job["id"],
        application_id=application["id"],
        headers=headers,
        candidate_headers=candidate_headers,
        disclosure_level="basic",
    )

    await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )

    applicants = await client.get(
        f"/api/v1/shadow-jobs/mine/{job['id']}/applicants", headers=headers
    )
    profile = applicants.json()[0]
    assert profile["revealed_full_name"] == "Basic Applicant"
    assert profile["revealed_email"] is None
    assert profile["revealed_phone"] is None


async def test_reveal_on_one_job_does_not_leak_to_another_job_for_the_same_candidate(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@shadowreveal-crossjob.com")
    headers = auth_headers(owner["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers)
    job_b_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Another Role",
            "summary": "A second, unrelated role at the same company.",
            "description": "Full role description.",
        },
        headers=headers,
    )
    assert job_b_response.status_code == 201, job_b_response.text
    job_b = job_b_response.json()
    publish_b = await client.post(
        f"/api/v1/shadow-jobs/mine/{job_b['id']}/publish", headers=headers
    )
    assert publish_b.status_code == 200, publish_b.text
    job_b = publish_b.json()

    tokens = await candidate_signup(
        client, email="applicant@shadowreveal-crossjob.com", full_name="Cross Job Applicant"
    )
    candidate_headers = auth_headers(tokens["access_token"])
    passport_payload = {
        "headline": "Senior Product Leader",
        "summary": "A senior product leader.",
        "career_intent": "actively_looking",
        "personal_info": {
            "legal_name": "Cross Job Applicant",
            "phone": "+44 20 7946 0958",
        },
    }
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=passport_payload, headers=candidate_headers
    )
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text

    apply_a = await client.post(
        f"/api/v1/shadow-jobs/board/{job_a['id']}/apply", headers=candidate_headers
    )
    assert apply_a.status_code == 201, apply_a.text
    application_a = apply_a.json()
    apply_b = await client.post(
        f"/api/v1/shadow-jobs/board/{job_b['id']}/apply", headers=candidate_headers
    )
    assert apply_b.status_code == 201, apply_b.text

    # Reveal only on job A.
    await _request_and_approve_reveal(
        client,
        job_id=job_a["id"],
        application_id=application_a["id"],
        headers=headers,
        candidate_headers=candidate_headers,
    )
    await client.get(
        f"/api/v1/shadow-reveal/mine/{job_a['id']}/applicants/{application_a['id']}",
        headers=await step_up_headers(client, headers=headers),
    )

    profile_a = (
        await client.get(f"/api/v1/shadow-jobs/mine/{job_a['id']}/applicants", headers=headers)
    ).json()[0]
    assert profile_a["revealed_full_name"] == "Cross Job Applicant"

    # Job B's application for the SAME candidate must remain fully anonymous -- reveal is
    # per-application, never global to the candidate.
    profile_b = (
        await client.get(f"/api/v1/shadow-jobs/mine/{job_b['id']}/applicants", headers=headers)
    ).json()[0]
    assert profile_b["revealed_full_name"] is None
    assert profile_b["callsign"] != application_a["callsign"]

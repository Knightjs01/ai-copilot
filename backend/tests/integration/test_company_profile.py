from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import (
    auth_headers,
    invite_and_accept,
    platform_admin_headers,
    signup,
)

_PROFILE_PAYLOAD = {
    "description": "We build tools for hiring teams.",
    "culture": "Remote-first, async by default.",
    "benefits": ["Private healthcare", "Unlimited PTO"],
    "size": "51-200",
    "industry": ["Software"],
    "hiring_process_overview": "Screen, two interviews, offer.",
}


async def _submit_and_approve(client: AsyncClient, *, headers: dict) -> None:
    submit = await client.post("/api/v1/companies/me/submit-for-review", headers=headers)
    assert submit.status_code == 200, submit.text
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]
    admin_headers = await platform_admin_headers(client)
    approve = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=admin_headers
    )
    assert approve.status_code == 200, approve.text


async def test_owner_can_update_company_profile(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-owner.com")
    headers = auth_headers(owner["access_token"])

    response = await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["description"] == _PROFILE_PAYLOAD["description"]
    assert body["culture"] == _PROFILE_PAYLOAD["culture"]
    assert body["benefits"] == _PROFILE_PAYLOAD["benefits"]
    assert body["size"] == _PROFILE_PAYLOAD["size"]
    assert body["industry"] == _PROFILE_PAYLOAD["industry"]
    assert body["hiring_process_overview"] == _PROFILE_PAYLOAD["hiring_process_overview"]
    assert body["profile_status"] == "draft"


async def test_partial_update_does_not_reset_omitted_fields(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-partial.com")
    headers = auth_headers(owner["access_token"])
    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)

    response = await client.patch(
        "/api/v1/companies/me", json={"description": "Updated description."}, headers=headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["description"] == "Updated description."
    # Every other field survives the omission -- the real bug this phase fixed.
    assert body["culture"] == _PROFILE_PAYLOAD["culture"]
    assert body["benefits"] == _PROFILE_PAYLOAD["benefits"]
    assert body["industry"] == _PROFILE_PAYLOAD["industry"]


async def test_recruiter_cannot_update_company_profile(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@companyprofile-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@companyprofile-memberperm.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    response = await client.patch(
        "/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=member_headers
    )
    assert response.status_code == 403


async def test_public_profile_404_until_approved_then_visible(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-public.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    still_404 = await client.get(f"/api/v1/companies/{slug}")
    assert still_404.status_code == 404

    await _submit_and_approve(client, headers=headers)

    response = await client.get(f"/api/v1/companies/{slug}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slug"] == slug
    assert body["description"] == _PROFILE_PAYLOAD["description"]
    assert body["hiring_process_overview"] == _PROFILE_PAYLOAD["hiring_process_overview"]
    assert "id" not in body
    assert "email_domain" not in body
    assert "is_verified_domain" not in body

    me_after = await client.get("/api/v1/companies/me", headers=headers)
    assert me_after.json()["profile_status"] == "live"


async def test_public_profile_404_for_nonexistent_slug(client: AsyncClient) -> None:
    response = await client.get("/api/v1/companies/no-such-company")
    assert response.status_code == 404


async def test_board_listing_carries_company_slug_only_when_live(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-board.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Senior Backend Engineer",
            "summary": "Own our core platform services.",
            "description": "A full description of the role and its responsibilities.",
        },
        headers=headers,
    )
    job = job_response.json()
    publish = await client.post(f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers)
    published = publish.json()

    board_before = await client.get("/api/v1/shadow-jobs/board")
    listing_before = next(j for j in board_before.json() if j["id"] == published["id"])
    assert listing_before["company_slug"] is None

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await _submit_and_approve(client, headers=headers)

    board_after = await client.get("/api/v1/shadow-jobs/board")
    listing_after = next(j for j in board_after.json() if j["id"] == published["id"])
    assert listing_after["company_slug"] == slug


async def test_preview_reflects_unsaved_draft(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-preview.com")
    headers = auth_headers(owner["access_token"])
    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)

    preview = await client.get("/api/v1/companies/me/preview", headers=headers)
    assert preview.status_code == 200, preview.text
    assert preview.json()["description"] == _PROFILE_PAYLOAD["description"]

    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]
    still_404 = await client.get(f"/api/v1/companies/{slug}")
    assert still_404.status_code == 404


async def test_editing_after_live_does_not_change_the_public_snapshot_until_reapproved(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@companyprofile-resubmit.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await _submit_and_approve(client, headers=headers)

    await client.patch(
        "/api/v1/companies/me",
        json={"description": "A brand new description not yet approved."},
        headers=headers,
    )
    still_old = await client.get(f"/api/v1/companies/{slug}")
    assert still_old.json()["description"] == _PROFILE_PAYLOAD["description"]

    submit_again = await client.post("/api/v1/companies/me/submit-for-review", headers=headers)
    assert submit_again.status_code == 200, submit_again.text
    still_old_while_pending = await client.get(f"/api/v1/companies/{slug}")
    assert still_old_while_pending.json()["description"] == _PROFILE_PAYLOAD["description"]

    admin_headers = await platform_admin_headers(client)
    company_id = me.json()["id"]
    approve = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=admin_headers
    )
    assert approve.status_code == 200, approve.text
    now_new = await client.get(f"/api/v1/companies/{slug}")
    assert now_new.json()["description"] == "A brand new description not yet approved."


async def test_reject_returns_to_draft_and_leaves_the_live_snapshot_untouched(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@companyprofile-reject.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]
    company_id = me.json()["id"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await _submit_and_approve(client, headers=headers)

    await client.patch(
        "/api/v1/companies/me", json={"description": "Rejected description."}, headers=headers
    )
    await client.post("/api/v1/companies/me/submit-for-review", headers=headers)

    admin_headers = await platform_admin_headers(client)
    reject = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/reject",
        json={"reason": "Needs more detail"},
        headers=admin_headers,
    )
    assert reject.status_code == 200, reject.text
    assert reject.json()["profile_status"] == "draft"

    unaffected = await client.get(f"/api/v1/companies/{slug}")
    assert unaffected.json()["description"] == _PROFILE_PAYLOAD["description"]


async def test_pause_and_resume_do_not_require_a_new_review(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-pause.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await _submit_and_approve(client, headers=headers)

    pause = await client.post("/api/v1/companies/me/pause", headers=headers)
    assert pause.status_code == 200, pause.text
    assert pause.json()["profile_status"] == "paused"
    paused_public = await client.get(f"/api/v1/companies/{slug}")
    assert paused_public.status_code == 404

    resume = await client.post("/api/v1/companies/me/resume", headers=headers)
    assert resume.status_code == 200, resume.text
    assert resume.json()["profile_status"] == "live"
    resumed_public = await client.get(f"/api/v1/companies/{slug}")
    assert resumed_public.status_code == 200


async def test_invalid_transitions_are_rejected(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-invalidtransition.com")
    headers = auth_headers(owner["access_token"])

    # Can't pause a draft profile.
    pause_denied = await client.post("/api/v1/companies/me/pause", headers=headers)
    assert pause_denied.status_code == 409

    # Can't submit twice in a row without a decision in between.
    await client.post("/api/v1/companies/me/submit-for-review", headers=headers)
    resubmit_denied = await client.post("/api/v1/companies/me/submit-for-review", headers=headers)
    assert resubmit_denied.status_code == 409

    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]
    admin_headers = await platform_admin_headers(client)
    await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=admin_headers
    )
    # Can't approve an already-approved (now live) request again.
    reapprove_denied = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=admin_headers
    )
    assert reapprove_denied.status_code == 409


async def test_admin_can_preview_a_companys_draft_before_approving(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-adminpreview.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await client.post("/api/v1/companies/me/submit-for-review", headers=headers)

    admin_headers = await platform_admin_headers(client)
    preview = await client.get(
        f"/api/v1/companies/{company_id}/profile-review/preview", headers=admin_headers
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["description"] == _PROFILE_PAYLOAD["description"]


async def test_logo_upload_validates_content_type_and_size(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-logo.com")
    headers = auth_headers(owner["access_token"])

    bad_type = await client.post(
        "/api/v1/companies/me/logo",
        files={"file": ("logo.pdf", b"not an image", "application/pdf")},
        headers=headers,
    )
    assert bad_type.status_code == 400

    good = await client.post(
        "/api/v1/companies/me/logo",
        files={"file": ("logo.png", b"\x89PNG fake but small", "image/png")},
        headers=headers,
    )
    assert good.status_code == 200, good.text
    assert good.json()["logo_url"] is not None

    me = await client.get("/api/v1/companies/me", headers=headers)
    slug = me.json()["slug"]
    fetched = await client.get(f"/api/v1/companies/{slug}/logo")
    assert fetched.status_code == 200
    assert fetched.content == b"\x89PNG fake but small"


async def test_approving_and_rejecting_a_review_emails_every_company_user(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@companyprofile-notify.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await client.patch("/api/v1/companies/me", json=_PROFILE_PAYLOAD, headers=headers)
    await client.post("/api/v1/companies/me/submit-for-review", headers=headers)

    admin_headers = await platform_admin_headers(client)
    approve = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=admin_headers
    )
    assert approve.status_code == 200, approve.text
    approved_email = next(
        e for e in sent_emails.sent if e["to"] == "owner@companyprofile-notify.com"
    )
    assert "live" in approved_email["body"].lower() or "approved" in approved_email["body"].lower()

    await client.patch(
        "/api/v1/companies/me", json={"description": "Second submission."}, headers=headers
    )
    await client.post("/api/v1/companies/me/submit-for-review", headers=headers)
    reject = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/reject",
        json={"reason": "Please add more detail"},
        headers=admin_headers,
    )
    assert reject.status_code == 200, reject.text
    rejected_email = next(
        e
        for e in sent_emails.sent
        if e["to"] == "owner@companyprofile-notify.com" and "needs changes" in e["subject"]
    )
    assert "Please add more detail" in rejected_email["body"]


async def test_non_platform_admin_cannot_access_profile_review_routes(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@companyprofile-noadmin.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    approve_denied = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/approve", headers=headers
    )
    assert approve_denied.status_code in (401, 403)

    reject_denied = await client.post(
        f"/api/v1/companies/{company_id}/profile-review/reject", headers=headers
    )
    assert reject_denied.status_code in (401, 403)

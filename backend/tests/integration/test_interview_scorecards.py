from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from tests.conftest import FakeInterviewScorecardLLMClient
from tests.integration.helpers import (
    auth_headers,
    candidate_signup,
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


async def _get_user_id(client: AsyncClient, *, headers: dict) -> str:
    me = await client.get("/api/v1/auth/me", headers=headers)
    return me.json()["id"]


async def _setup_interview(
    client: AsyncClient, *, sent_emails, domain: str, assign_interviewer: bool = True
) -> dict:
    """Returns {owner_headers, job, application, interview, interviewer_headers, interviewer_id,
    candidate_headers}."""
    owner = await signup(client, email=f"owner@{domain}")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    application, candidate_headers = await _apply_with_new_candidate(
        client, job_id=job["id"], email=f"candidate@{domain}"
    )

    interviewer = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email=f"interviewer@{domain}",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    interviewer_headers = auth_headers(interviewer["access_token"])
    interviewer_id = await _get_user_id(client, headers=interviewer_headers)

    schedule_response = await client.post(
        f"/api/v1/interviews/mine/{job['id']}/applicants/{application['id']}",
        json={
            "scheduled_at": _future_iso(),
            "interviewer_user_ids": [interviewer_id] if assign_interviewer else [],
        },
        headers=owner_headers,
    )
    assert schedule_response.status_code == 201, schedule_response.text
    interview = schedule_response.json()

    return {
        "owner_headers": owner_headers,
        "job": job,
        "application": application,
        "interview": interview,
        "interviewer_headers": interviewer_headers,
        "interviewer_id": interviewer_id,
        "candidate_headers": candidate_headers,
    }


def _scorecard_url(setup: dict, *, suffix: str = "") -> str:
    return (
        f"/api/v1/interviews/mine/{setup['job']['id']}/applicants/"
        f"{setup['application']['id']}/{setup['interview']['id']}/scorecard{suffix}"
    )


async def test_participant_interviewer_can_generate_and_save_scorecard(
    client: AsyncClient, sent_emails
) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-basic.com")

    generate_response = await client.post(
        _scorecard_url(setup, suffix="/generate"),
        json={"notes": "Communicated clearly, strong technical depth, some gaps on ownership."},
        headers=setup["interviewer_headers"],
    )
    assert generate_response.status_code == 200, generate_response.text
    draft = generate_response.json()
    assert len(draft["competency_scores"]) == 3
    assert draft["overall_recommendation"] == "Hire"

    save_response = await client.put(
        _scorecard_url(setup),
        json={
            "notes": "Communicated clearly, strong technical depth, some gaps on ownership.",
            "competency_scores": draft["competency_scores"],
            "overall_recommendation": draft["overall_recommendation"],
        },
        headers=setup["interviewer_headers"],
    )
    assert save_response.status_code == 200, save_response.text
    saved = save_response.json()
    assert saved["submitted_by_user_id"] == setup["interviewer_id"]
    assert len(saved["competency_scores"]) == 3


async def test_non_participant_without_schedule_permission_gets_404(
    client: AsyncClient, sent_emails
) -> None:
    setup = await _setup_interview(
        client, sent_emails=sent_emails, domain="scorecard-nonparticipant.com"
    )
    other_interviewer = await invite_and_accept(
        client,
        inviter_headers=setup["owner_headers"],
        email="other@scorecard-nonparticipant.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    other_headers = auth_headers(other_interviewer["access_token"])

    generate_response = await client.post(
        _scorecard_url(setup, suffix="/generate"),
        json={"notes": "Some notes."},
        headers=other_headers,
    )
    assert generate_response.status_code == 404

    save_response = await client.put(
        _scorecard_url(setup),
        json={
            "notes": "Some notes.",
            "competency_scores": [{"competency": "X", "rating": "Strong", "evidence": "Y"}],
            "overall_recommendation": "Hire",
        },
        headers=other_headers,
    )
    assert save_response.status_code == 404


async def test_saving_marks_interview_completed(client: AsyncClient, sent_emails) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-complete.com")
    assert setup["interview"]["status"] == "scheduled"

    await client.put(
        _scorecard_url(setup),
        json={
            "notes": "Notes.",
            "competency_scores": [{"competency": "X", "rating": "Strong", "evidence": "Y"}],
            "overall_recommendation": "Hire",
        },
        headers=setup["interviewer_headers"],
    )

    interview_view = await client.get(
        f"/api/v1/interviews/mine/{setup['job']['id']}/applicants/{setup['application']['id']}",
        headers=setup["owner_headers"],
    )
    interviews = interview_view.json()
    assert interviews[0]["status"] == "completed"


async def test_resaving_upserts_in_place(client: AsyncClient, sent_emails) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-upsert.com")

    first = await client.put(
        _scorecard_url(setup),
        json={
            "notes": "First pass notes.",
            "competency_scores": [{"competency": "X", "rating": "Weak", "evidence": "Y"}],
            "overall_recommendation": "No Hire",
        },
        headers=setup["interviewer_headers"],
    )
    assert first.status_code == 200

    second = await client.put(
        _scorecard_url(setup),
        json={
            "notes": "Revised notes after reflection.",
            "competency_scores": [{"competency": "X", "rating": "Strong", "evidence": "Z"}],
            "overall_recommendation": "Hire",
        },
        headers=setup["interviewer_headers"],
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["overall_recommendation"] == "Hire"

    listing = await client.get(_scorecard_url(setup, suffix="s"), headers=setup["owner_headers"])
    assert len(listing.json()) == 1
    assert listing.json()[0]["notes"] == "Revised notes after reflection."


async def test_two_interviewers_get_independent_rows(client: AsyncClient, sent_emails) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-multi.com")

    second_interviewer = await invite_and_accept(
        client,
        inviter_headers=setup["owner_headers"],
        email="second@scorecard-multi.com",
        role="Interviewer",
        sent_emails=sent_emails,
    )
    second_headers = auth_headers(second_interviewer["access_token"])
    second_id = await _get_user_id(client, headers=second_headers)

    # Assign both interviewers so both can pass the resource-scoping check.
    await client.patch(
        f"/api/v1/interviews/mine/{setup['job']['id']}/applicants/"
        f"{setup['application']['id']}/{setup['interview']['id']}",
        json={"interviewer_user_ids": [setup["interviewer_id"], second_id]},
        headers=setup["owner_headers"],
    )

    await client.put(
        _scorecard_url(setup),
        json={
            "notes": "First interviewer notes.",
            "competency_scores": [{"competency": "X", "rating": "Strong", "evidence": "Y"}],
            "overall_recommendation": "Hire",
        },
        headers=setup["interviewer_headers"],
    )
    await client.put(
        _scorecard_url(setup),
        json={
            "notes": "Second interviewer notes.",
            "competency_scores": [{"competency": "X", "rating": "Weak", "evidence": "Y"}],
            "overall_recommendation": "No Hire",
        },
        headers=second_headers,
    )

    listing = await client.get(_scorecard_url(setup, suffix="s"), headers=setup["owner_headers"])
    assert listing.status_code == 200
    scorecards = listing.json()
    assert len(scorecards) == 2
    submitters = {s["submitted_by_user_id"] for s in scorecards}
    assert submitters == {setup["interviewer_id"], second_id}


async def test_generate_never_persists(client: AsyncClient, sent_emails) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-preview.com")

    await client.post(
        _scorecard_url(setup, suffix="/generate"),
        json={"notes": "Some notes to preview a scorecard from."},
        headers=setup["interviewer_headers"],
    )

    listing = await client.get(_scorecard_url(setup, suffix="s"), headers=setup["owner_headers"])
    assert listing.status_code == 200
    assert listing.json() == []


async def test_notes_are_redacted_before_reaching_llm_client(
    client: AsyncClient,
    sent_emails,
    fake_interview_scorecard_llm_client: FakeInterviewScorecardLLMClient,
) -> None:
    setup = await _setup_interview(client, sent_emails=sent_emails, domain="scorecard-redact.com")

    # Drive a real identity reveal so ShadowApplication.revealed_full_name is populated --
    # redact_text only strips a name it's told to look for, and with nothing revealed yet the
    # known_full_name fallback is "" (no name-specific pass), which would make this assertion
    # trivially true for the wrong reason.
    await client.post(
        f"/api/v1/shadow-reveal/mine/{setup['job']['id']}/applicants/{setup['application']['id']}/request",
        json={},
        headers=setup["owner_headers"],
    )
    candidate_headers = setup["candidate_headers"]
    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{setup['application']['id']}/respond",
        json={"approve": True},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text
    reveal_view = await client.get(
        f"/api/v1/shadow-reveal/mine/{setup['job']['id']}/applicants/{setup['application']['id']}",
        headers=await step_up_headers(client, headers=setup["owner_headers"]),
    )
    assert reveal_view.status_code == 200, reveal_view.text
    assert reveal_view.json()["full_name"] == "Jamie Candidate"

    notes_with_name = (
        "Jamie Candidate came across as very strong technically; Jamie also communicated well."
    )
    response = await client.post(
        _scorecard_url(setup, suffix="/generate"),
        json={"notes": notes_with_name},
        headers=setup["interviewer_headers"],
    )
    assert response.status_code == 200, response.text

    assert fake_interview_scorecard_llm_client.calls, "expected the fake client to be called"
    sent_notes = fake_interview_scorecard_llm_client.calls[-1]["notes"]
    assert "Jamie" not in sent_notes

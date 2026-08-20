from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, candidate_signup, invite_and_accept, signup

_JOB_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "summary": "Own our core platform services.",
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


async def _build_and_approve_passport(
    client: AsyncClient,
    *,
    email: str,
    full_name: str = "Jamie Candidate",
    visibility: str | None = None,
    career_intent: str | None = None,
    approve: bool = True,
) -> dict:
    tokens = await candidate_signup(client, email=email, full_name=full_name)
    candidate_headers = auth_headers(tokens["access_token"])
    payload = {
        "headline": "Senior Backend Engineer",
        "summary": "Backend engineer with experience building scalable services.",
        "skills": ["Backend Development"],
        "personal_info": {"legal_name": full_name},
        "career_entries": [],
    }
    if visibility is not None:
        payload["visibility"] = visibility
    if career_intent is not None:
        payload["career_intent"] = career_intent
    save_response = await client.put(
        "/api/v1/phantom-passport/me", json=payload, headers=candidate_headers
    )
    assert save_response.status_code == 200, save_response.text
    if approve:
        approve_response = await client.post(
            "/api/v1/phantom-passport/me/approve", headers=candidate_headers
        )
        assert approve_response.status_code == 200, approve_response.text
    return candidate_headers


async def test_search_includes_only_discoverable_approved_candidates(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@candidatesearch-basic.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)

    await _build_and_approve_passport(
        client,
        email="private@candidatesearch-basic.com",
        full_name="Private Candidate",
        visibility="private",
    )
    await _build_and_approve_passport(
        client,
        email="matchonly@candidatesearch-basic.com",
        full_name="Match Only Candidate",
        visibility="match_only",
    )
    await _build_and_approve_passport(
        client,
        email="discoverable@candidatesearch-basic.com",
        full_name="Discoverable Candidate",
        visibility="discoverable",
    )

    response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=owner_headers
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert len(results) == 2
    headlines = {r["callsign"] for r in results}
    assert len(headlines) == 2  # both got real, distinct passport callsigns
    for result in results:
        assert result["match_tier"] == "Strong Match"
        assert result["match_score"] == 72
        # Anonymized only -- no PII field could ever appear here.
        assert "candidate_user_id" not in result
        assert "email" not in result
        assert "full_name" not in result


async def test_unapproved_passport_never_appears(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@candidatesearch-unapproved.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)

    await _build_and_approve_passport(
        client,
        email="unapproved@candidatesearch-unapproved.com",
        visibility="discoverable",
        approve=False,
    )

    response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=owner_headers
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_not_looking_candidate_never_appears_even_if_discoverable(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@candidatesearch-notlooking.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)

    await _build_and_approve_passport(
        client,
        email="notlooking@candidatesearch-notlooking.com",
        visibility="discoverable",
        career_intent="not_looking",
    )

    response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=owner_headers
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_member_can_search_candidates(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@candidatesearch-memberperm.com")
    owner_headers = auth_headers(owner["access_token"])
    job = await _create_and_publish_job(client, headers=owner_headers)
    await _build_and_approve_passport(
        client, email="candidate@candidatesearch-memberperm.com", visibility="discoverable"
    )

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@candidatesearch-memberperm.com",
        role="Member",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    response = await client.get(
        f"/api/v1/matches/mine/{job['id']}/candidates", headers=member_headers
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


async def test_cross_tenant_search_is_isolated(client: AsyncClient) -> None:
    owner_a = await signup(client, email="owner-a@candidatesearch-isolation.com")
    headers_a = auth_headers(owner_a["access_token"])
    job_a = await _create_and_publish_job(client, headers=headers_a)

    owner_b = await signup(client, email="owner-b@candidatesearch-isolation.com")
    headers_b = auth_headers(owner_b["access_token"])

    response = await client.get(f"/api/v1/matches/mine/{job_a['id']}/candidates", headers=headers_b)
    assert response.status_code == 404

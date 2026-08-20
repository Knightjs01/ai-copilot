from httpx import AsyncClient

from tests.integration.helpers import auth_headers, candidate_signup


async def _build_and_approve_passport(client: AsyncClient, *, email: str) -> str:
    tokens = await candidate_signup(client, email=email, full_name="Jamie Candidate")
    headers = auth_headers(tokens["access_token"])
    payload = {
        "headline": "Senior Backend Engineer",
        "seniority": "Senior",
        "summary": "Backend engineer with experience building scalable services.",
        "skills": ["Backend Development"],
        "personal_info": {"legal_name": "Jamie Candidate"},
        "career_entries": [],
    }
    save_response = await client.put("/api/v1/phantom-passport/me", json=payload, headers=headers)
    assert save_response.status_code == 200, save_response.text
    approve_response = await client.post("/api/v1/phantom-passport/me/approve", headers=headers)
    assert approve_response.status_code == 200, approve_response.text

    me = await client.get("/api/v1/phantom-passport/me", headers=headers)
    callsign = me.json()["callsign"]
    assert callsign
    return callsign


async def test_verification_returns_public_shape_with_no_pii(client: AsyncClient) -> None:
    callsign = await _build_and_approve_passport(client, email="candidate@verify-basic.com")

    response = await client.get(f"/api/v1/phantom-passport/verify/{callsign}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["callsign"] == callsign
    assert body["headline"] == "Senior Backend Engineer"
    assert body["seniority"] == "Senior"
    assert body["verification_status"] == "unverified"
    assert isinstance(body["completion_percentage"], int)
    assert "personal_info" not in body
    assert "career_entries" not in body
    assert "id" not in body


async def test_verification_404s_for_nonexistent_callsign(client: AsyncClient) -> None:
    response = await client.get("/api/v1/phantom-passport/verify/no-such-callsign")
    assert response.status_code == 404

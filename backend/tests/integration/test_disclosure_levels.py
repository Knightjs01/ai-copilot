from httpx import AsyncClient

from tests.integration.helpers import (
    auth_headers,
    candidate_signup,
    create_project,
    signup,
    step_up_headers,
)


async def _create_candidate(
    client: AsyncClient, *, headers: dict, project_id: str, full_name: str, **extra: object
) -> dict:
    response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_id, "full_name": full_name, **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_identity_vault_basic_disclosure_hides_contact_and_employer(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@disclosure-basic.com", company_name="Disclosure Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate = await _create_candidate(
        client,
        headers=headers,
        project_id=project["id"],
        full_name="Basic Disclosure Candidate",
        email="basic@example.com",
        phone="555-0100",
    )
    await client.patch(
        f"/api/v1/identity-vault/candidates/{candidate['id']}",
        json={"current_employer": "Acme Corp", "location": "Hull, UK"},
        headers=headers,
    )

    reveal_response = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Sanity check on fit", "disclosure_level": "basic"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 200, reveal_response.text
    snapshot = reveal_response.json()
    assert snapshot["disclosure_level"] == "basic"
    assert snapshot["full_name"] == "Basic Disclosure Candidate"
    assert snapshot["location"] == "Hull, UK"
    assert snapshot["email"] is None
    assert snapshot["phone"] is None
    assert snapshot["current_employer"] is None
    assert snapshot["expected_salary"] is None


async def test_identity_vault_contact_disclosure_includes_email_but_not_employer(
    client: AsyncClient,
) -> None:
    owner = await signup(
        client, email="owner@disclosure-contact.com", company_name="Disclosure Contact Co"
    )
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate = await _create_candidate(
        client,
        headers=headers,
        project_id=project["id"],
        full_name="Contact Disclosure Candidate",
        email="contact@example.com",
    )
    await client.patch(
        f"/api/v1/identity-vault/candidates/{candidate['id']}",
        json={"current_employer": "Acme Corp"},
        headers=headers,
    )

    reveal_response = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Reaching out", "disclosure_level": "contact"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 200, reveal_response.text
    snapshot = reveal_response.json()
    assert snapshot["disclosure_level"] == "contact"
    assert snapshot["email"] == "contact@example.com"
    assert snapshot["current_employer"] is None


async def test_identity_vault_reveal_defaults_to_full_disclosure(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@disclosure-default.com")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)
    candidate = await _create_candidate(
        client,
        headers=headers,
        project_id=project["id"],
        full_name="Default Disclosure Candidate",
        email="default@example.com",
    )

    reveal_response = await client.post(
        f"/api/v1/identity-vault/candidates/{candidate['id']}/reveal",
        json={"reason": "Background Checks"},
        headers=await step_up_headers(client, headers=headers),
    )
    assert reveal_response.status_code == 200, reveal_response.text
    assert reveal_response.json()["disclosure_level"] == "full"
    assert reveal_response.json()["email"] == "default@example.com"


async def test_shadow_reveal_candidate_can_approve_with_basic_disclosure_only(
    client: AsyncClient,
) -> None:
    owner = await signup(client, email="owner@shadow-disclosure.com")
    headers = auth_headers(owner["access_token"])
    job_response = await client.post(
        "/api/v1/shadow-jobs",
        json={
            "title": "Staff Engineer",
            "summary": "Own our core platform.",
            "description": "Full role description.",
        },
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()
    publish_response = await client.post(
        f"/api/v1/shadow-jobs/mine/{job['id']}/publish", headers=headers
    )
    assert publish_response.status_code == 200, publish_response.text

    tokens = await candidate_signup(client, email="applicant@shadow-disclosure.com")
    candidate_headers = auth_headers(tokens["access_token"])
    await client.put(
        "/api/v1/phantom-passport/me",
        json={
            "headline": "Staff Engineer",
            "personal_info": {"legal_name": "Discreet Applicant", "phone": "+44 20 7946 0958"},
            "career_entries": [
                {
                    "title": "VP Product",
                    "company_name": "Stripe",
                    "company_name_anonymized": "Global Payments Platform",
                    "is_current": True,
                }
            ],
        },
        headers=candidate_headers,
    )
    approve_response = await client.post(
        "/api/v1/phantom-passport/me/approve", headers=candidate_headers
    )
    assert approve_response.status_code == 200, approve_response.text
    apply_response = await client.post(
        f"/api/v1/shadow-jobs/board/{job['id']}/apply", headers=candidate_headers
    )
    assert apply_response.status_code == 201, apply_response.text
    application = apply_response.json()

    await client.post(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}/request",
        json={"reason": "Ready to move forward"},
        headers=headers,
    )

    approve_response = await client.post(
        f"/api/v1/shadow-reveal/applications/me/{application['id']}/respond",
        json={"approve": True, "disclosure_level": "basic"},
        headers=candidate_headers,
    )
    assert approve_response.status_code == 200, approve_response.text

    revealed_response = await client.get(
        f"/api/v1/shadow-reveal/mine/{job['id']}/applicants/{application['id']}",
        headers=await step_up_headers(client, headers=headers),
    )
    assert revealed_response.status_code == 200, revealed_response.text
    revealed = revealed_response.json()
    assert revealed["disclosure_level"] == "basic"
    assert revealed["full_name"] == "Discreet Applicant"
    assert revealed["email"] is None
    assert revealed["phone"] is None
    assert revealed["career_entries"] == []

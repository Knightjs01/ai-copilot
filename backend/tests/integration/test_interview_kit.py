from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import CapturingEmailSender, FakeInterviewKitLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup


async def _create_project_with_blueprint(
    client: AsyncClient, *, headers: dict, role_brief: str
) -> str:
    project = await create_project(client, headers=headers, title="Senior Backend Engineer")
    patch_response = await client.patch(
        f"/api/v1/projects/{project['id']}", json={"role_brief": role_brief}, headers=headers
    )
    assert patch_response.status_code == 200, patch_response.text
    blueprint_response = await client.post(
        f"/api/v1/projects/{project['id']}/hiring-blueprint", headers=headers
    )
    assert blueprint_response.status_code == 200, blueprint_response.text
    return project["id"]


async def test_generate_interview_kit_happy_path(
    client: AsyncClient, fake_interview_kit_llm_client: FakeInterviewKitLLMClient
) -> None:
    owner = await signup(client, email="owner@interviewkit.com", company_name="Kit Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client,
        headers=headers,
        role_brief="Looking for a senior backend engineer to lead our platform team.",
    )

    generate_response = await client.post(
        f"/api/v1/projects/{project_id}/interview-kit", headers=headers
    )
    assert generate_response.status_code == 200, generate_response.text
    kit = generate_response.json()

    # FakeHiringBlueprintLLMClient returns 1 must-have + 2 evaluation criteria == 3 questions.
    assert len(kit["questions"]) == 3
    assert kit["questions"][0]["source_type"] == "must_have"
    assert kit["questions"][0]["source_text"] == "Fake required skill"
    assert kit["questions"][1]["source_type"] == "evaluation_criterion"
    assert kit["questions"][1]["source_text"] == "Technical depth"
    assert kit["questions"][2]["source_type"] == "evaluation_criterion"
    assert kit["questions"][2]["source_text"] == "Collaboration"
    for question in kit["questions"]:
        assert question["question_text"]
        assert question["follow_up_prompts"] == ["Fake follow-up prompt"]
    assert kit["model_used"] == "claude-sonnet-5"

    assert len(fake_interview_kit_llm_client.calls) == 1
    must_haves, criteria = fake_interview_kit_llm_client.calls[0]
    assert must_haves == ["Fake required skill"]
    assert criteria == ["Technical depth", "Collaboration"]

    get_response = await client.get(f"/api/v1/projects/{project_id}/interview-kit", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == kit["id"]


async def test_generate_without_blueprint_fails(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@nokitblueprint.com", company_name="No Kit Blueprint")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.post(f"/api/v1/projects/{project['id']}/interview-kit", headers=headers)
    assert response.status_code == 400  # MissingHiringBlueprintError


async def test_generate_produces_one_question_per_blueprint_item(
    client: AsyncClient, fake_interview_kit_llm_client: FakeInterviewKitLLMClient
) -> None:
    owner = await signup(client, email="owner@kitcount.com", company_name="Kit Count Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=headers, role_brief="A role brief."
    )

    generate_response = await client.post(
        f"/api/v1/projects/{project_id}/interview-kit", headers=headers
    )
    assert generate_response.status_code == 200, generate_response.text
    kit = generate_response.json()

    # Every grounding item — must-haves in order, then evaluation criteria in order — must map
    # to exactly one question, no more, no fewer.
    must_haves, criteria = fake_interview_kit_llm_client.calls[0]
    expected_sources = [("must_have", text) for text in must_haves] + [
        ("evaluation_criterion", text) for text in criteria
    ]
    actual_sources = [(q["source_type"], q["source_text"]) for q in kit["questions"]]
    assert actual_sources == expected_sources


async def test_member_can_view_but_not_trigger_generation(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@kitperms.com", company_name="Kit Perms")
    owner_headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=owner_headers, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/interview-kit", headers=owner_headers)

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@kitperms.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    generate_denied = await client.post(
        f"/api/v1/projects/{project_id}/interview-kit", headers=member_headers
    )
    assert generate_denied.status_code == 403

    view_allowed = await client.get(
        f"/api/v1/projects/{project_id}/interview-kit", headers=member_headers
    )
    assert view_allowed.status_code == 200


async def test_rls_blocks_cross_tenant_interview_kit_reads(client: AsyncClient) -> None:
    from app.db.base import engine

    owner_a = await signup(client, email="owner@rlskit-a.com", company_name="RLS Kit A")
    headers_a = auth_headers(owner_a["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=headers_a, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/interview-kit", headers=headers_a)

    owner_b = await signup(client, email="owner@rlskit-b.com", company_name="RLS Kit B")
    me_a = await client.get("/api/v1/auth/me", headers=headers_a)
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(owner_b["access_token"]))
    company_a_id = me_a.json()["company_id"]
    company_b_id = me_b.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            import uuid as uuid_module

            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_b_id)}'")
            )
            cross_tenant_query = await conn.execute(
                text("SELECT id FROM interview_kits WHERE company_id = :cid"),
                {"cid": company_a_id},
            )
            assert cross_tenant_query.fetchall() == []


async def test_update_interview_kit_selection_happy_path(
    client: AsyncClient, fake_interview_kit_llm_client: FakeInterviewKitLLMClient
) -> None:
    owner = await signup(client, email="owner@kitselect.com", company_name="Kit Select Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=headers, role_brief="A role brief."
    )
    generate_response = await client.post(
        f"/api/v1/projects/{project_id}/interview-kit", headers=headers
    )
    kit = generate_response.json()
    assert all(q["included"] is False for q in kit["questions"])

    select_response = await client.patch(
        f"/api/v1/projects/{project_id}/interview-kit/selection",
        json={"included_flags": [True, False, True]},
        headers=headers,
    )
    assert select_response.status_code == 200, select_response.text
    updated = select_response.json()["questions"]
    assert [q["included"] for q in updated] == [True, False, True]
    # Everything else about each question is untouched by a selection update.
    assert [q["question_text"] for q in updated] == [q["question_text"] for q in kit["questions"]]

    # Persisted -- a fresh GET reflects it.
    get_response = await client.get(f"/api/v1/projects/{project_id}/interview-kit", headers=headers)
    assert [q["included"] for q in get_response.json()["questions"]] == [True, False, True]


async def test_update_interview_kit_selection_rejects_mismatched_length(
    client: AsyncClient, fake_interview_kit_llm_client: FakeInterviewKitLLMClient
) -> None:
    owner = await signup(client, email="owner@kitmismatch.com", company_name="Kit Mismatch Co")
    headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=headers, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/interview-kit", headers=headers)

    response = await client.patch(
        f"/api/v1/projects/{project_id}/interview-kit/selection",
        json={"included_flags": [True, False]},  # kit has 3 questions, not 2
        headers=headers,
    )
    assert response.status_code == 400


async def test_update_interview_kit_selection_requires_permission(
    client: AsyncClient,
    sent_emails: CapturingEmailSender,
    fake_interview_kit_llm_client: FakeInterviewKitLLMClient,
) -> None:
    owner = await signup(client, email="owner@kitselectperm.com", company_name="Kit Select Perm")
    owner_headers = auth_headers(owner["access_token"])
    project_id = await _create_project_with_blueprint(
        client, headers=owner_headers, role_brief="A role brief."
    )
    await client.post(f"/api/v1/projects/{project_id}/interview-kit", headers=owner_headers)

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@kitselectperm.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    response = await client.patch(
        f"/api/v1/projects/{project_id}/interview-kit/selection",
        json={"included_flags": [True, False, True]},
        headers=member_headers,
    )
    assert response.status_code == 403


async def test_app_auth_role_has_no_grants_on_interview_kits() -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    auth_engine = create_async_engine(settings.auth_database_url)
    try:
        async with auth_engine.connect() as conn:
            try:
                await conn.execute(text("SELECT 1 FROM interview_kits LIMIT 1"))
                raised = False
            except DBAPIError:
                raised = True
            assert raised, "app_auth should not have SELECT privilege on interview_kits"
    finally:
        await auth_engine.dispose()

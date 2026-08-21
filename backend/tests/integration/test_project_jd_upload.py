from io import BytesIO

from docx import Document
from httpx import AsyncClient

from tests.conftest import CapturingEmailSender, FakeProjectsLLMClient
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup

_JD_TEXT = "We are hiring a Senior Backend Engineer to own our event-processing pipeline."


def _build_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_upload_jd_returns_a_preview_without_saving(
    client: AsyncClient, fake_projects_llm_client: FakeProjectsLLMClient
) -> None:
    """upload_jd is a preview only -- see phantom_passport.service.py::parse_cv for the identical
    convention this mirrors. Nothing is persisted until a separate PATCH."""
    owner = await signup(client, email="owner@jdupload.com", company_name="JD Upload Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    jd_bytes = _build_docx_bytes(_JD_TEXT)
    response = await client.post(
        f"/api/v1/projects/{project['id']}/jd",
        files={
            "file": (
                "jd.docx",
                jd_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["role_brief"] == _JD_TEXT
    assert preview["seniority"] == "Senior"
    assert preview["location"] == "Remote (UK)"
    assert preview["salary_min"] == 90000
    assert preview["salary_max"] == 110000
    assert len(fake_projects_llm_client.calls) == 1
    assert fake_projects_llm_client.calls[0] == _JD_TEXT

    # Nothing saved yet -- the project is still exactly as it was created.
    get_before = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert get_before.json()["role_brief"] is None
    assert get_before.json()["seniority"] is None
    assert get_before.json()["salary_min"] is None

    # The recruiter reviews the preview and saves explicitly.
    patch_response = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={
            "role_brief": preview["role_brief"],
            "seniority": preview["seniority"],
            "location": preview["location"],
            "salary_min": preview["salary_min"],
            "salary_max": preview["salary_max"],
        },
        headers=headers,
    )
    assert patch_response.status_code == 200, patch_response.text

    get_after = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    saved = get_after.json()
    assert saved["role_brief"] == _JD_TEXT
    assert saved["seniority"] == "Senior"
    assert saved["location"] == "Remote (UK)"
    assert saved["salary_min"] == 90000
    assert saved["salary_max"] == 110000


async def test_upload_jd_rejects_unsupported_content_type(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@jdwrongtype.com", company_name="JD Wrong Type Co")
    headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=headers)

    response = await client.post(
        f"/api/v1/projects/{project['id']}/jd",
        files={"file": ("jd.exe", b"not a jd", "application/x-msdownload")},
        headers=headers,
    )
    assert response.status_code == 400


async def test_member_cannot_upload_jd(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    owner = await signup(client, email="owner@jdperms.com", company_name="JD Perms Co")
    owner_headers = auth_headers(owner["access_token"])
    project = await create_project(client, headers=owner_headers)

    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@jdperms.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    jd_bytes = _build_docx_bytes(_JD_TEXT)
    response = await client.post(
        f"/api/v1/projects/{project['id']}/jd",
        files={
            "file": (
                "jd.docx",
                jd_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=member_headers,
    )
    assert response.status_code == 403

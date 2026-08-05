from io import BytesIO

from docx import Document
from httpx import AsyncClient

from tests.conftest import CapturingEmailSender
from tests.integration.helpers import auth_headers, create_project, invite_and_accept, signup

_JD_TEXT = "We are hiring a Senior Backend Engineer to own our event-processing pipeline."


def _build_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_upload_jd_populates_role_brief(client: AsyncClient) -> None:
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
    assert response.json()["role_brief"] == _JD_TEXT

    get_response = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert get_response.json()["role_brief"] == _JD_TEXT


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
        role="Member",
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

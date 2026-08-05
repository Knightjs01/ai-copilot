from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.auth.email import BrevoEmailSender, EmailSendError


def _make_sender() -> BrevoEmailSender:
    return BrevoEmailSender(api_key="fake-key", sender_email="noreply@example.com")


def _fake_response(status_code: int, text: str = "") -> SimpleNamespace:
    return SimpleNamespace(status_code=status_code, text=text)


async def test_send_posts_expected_payload_to_brevo() -> None:
    sender = _make_sender()
    mock_post = AsyncMock(return_value=_fake_response(201))

    with patch("httpx.AsyncClient.post", mock_post):
        await sender.send(to="jordan@example.com", subject="Hello", body="Body text")

    mock_post.assert_awaited_once()
    call_args, call_kwargs = mock_post.await_args
    assert call_args[0] == "https://api.brevo.com/v3/smtp/email"
    assert call_kwargs["headers"]["api-key"] == "fake-key"
    payload = call_kwargs["json"]
    assert payload["sender"] == {"email": "noreply@example.com"}
    assert payload["to"] == [{"email": "jordan@example.com"}]
    assert payload["subject"] == "Hello"
    assert "Body text" in payload["htmlContent"]


async def test_send_raises_on_non_2xx_response() -> None:
    sender = _make_sender()
    mock_post = AsyncMock(return_value=_fake_response(400, "invalid sender"))

    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(EmailSendError):
            await sender.send(to="jordan@example.com", subject="Hello", body="Body text")

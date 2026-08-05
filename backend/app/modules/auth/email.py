import logging
from typing import Protocol

import httpx

logger = logging.getLogger("app.auth.email")

_BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


class EmailSendError(Exception):
    """Raised when a real provider rejects or fails to send — deliberately not swallowed, an
    invite that silently never arrives is worse than one that errors loudly."""


class ConsoleEmailSender:
    """Logs emails instead of sending them. Used for local dev and tests (get_email_sender()
    falls back to this whenever BREVO_API_KEY isn't set) — nothing outside this module needs to
    change to swap providers, callers only depend on the EmailSender protocol."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)


class BrevoEmailSender:
    """Real EmailSender implementation, backed by Brevo's transactional email API. sender_email
    must already be a verified sender/domain in the Brevo account — Brevo rejects sends from
    unverified senders."""

    def __init__(self, *, api_key: str, sender_email: str) -> None:
        self._api_key = api_key
        self._sender_email = sender_email

    async def send(self, *, to: str, subject: str, body: str) -> None:
        # body is currently always plain text (see build_*_email below) — sent as htmlContent
        # since Brevo requires either htmlContent or textContent; wrapping in <pre> preserves the
        # plain-text link formatting without needing a separate HTML template per email type.
        html_content = f"<pre style='font-family: inherit; white-space: pre-wrap;'>{body}</pre>"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _BREVO_API_URL,
                headers={
                    "api-key": self._api_key,
                    "content-type": "application/json",
                    "accept": "application/json",
                },
                json={
                    "sender": {"email": self._sender_email},
                    "to": [{"email": to}],
                    "subject": subject,
                    "htmlContent": html_content,
                },
            )
        if response.status_code >= 300:
            raise EmailSendError(
                f"Brevo rejected the email to {to!r}: {response.status_code} {response.text}"
            )


def build_verification_email(*, verify_url: str) -> tuple[str, str]:
    subject = "Verify your AI Interview Copilot email"
    body = (
        f"Welcome! Please verify your email by visiting:\n\n{verify_url}\n\nThis link expires soon."
    )
    return subject, body


def build_password_reset_email(*, reset_url: str) -> tuple[str, str]:
    subject = "Reset your AI Interview Copilot password"
    body = (
        f"We received a request to reset your password. Visit:\n\n{reset_url}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )
    return subject, body


def build_invite_email(*, company_name: str, accept_url: str) -> tuple[str, str]:
    subject = f"You've been invited to join {company_name} on AI Interview Copilot"
    body = f"You've been invited to join {company_name}. Accept your invite:\n\n{accept_url}"
    return subject, body

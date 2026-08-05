import logging
from typing import Protocol

logger = logging.getLogger("app.auth.email")


class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Logs emails instead of sending them. Swap for a real provider (SendGrid/SES/SMTP) later —
    nothing outside this module needs to change, callers only depend on the EmailSender protocol."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)


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

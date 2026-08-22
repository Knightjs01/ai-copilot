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


def build_workspace_approved_email(*, company_name: str) -> tuple[str, str]:
    subject = "Your Phantom workspace is ready"
    body = (
        f"Good news — Phantom has approved {company_name}'s workspace request.\n\n"
        "You can now log in with the email and password you used to request access."
    )
    return subject, body


def build_workspace_rejected_email(*, company_name: str, reason: str | None) -> tuple[str, str]:
    subject = "Your Phantom access request"
    reason_line = f"\n\nReason: {reason}" if reason else ""
    body = (
        f"We're unable to approve a Phantom workspace for {company_name} at this time."
        f"{reason_line}\n\nIf you believe this is a mistake, please contact Phantom support."
    )
    return subject, body


def build_info_requested_email(*, company_name: str, message: str) -> tuple[str, str]:
    subject = "Phantom needs more information about your access request"
    body = (
        f"We're reviewing your access request for {company_name} and need a bit more "
        f"information before we can proceed:\n\n{message}\n\n"
        "Reply to this email with the requested details."
    )
    return subject, body


def build_profile_approved_email(*, company_name: str, profile_url: str) -> tuple[str, str]:
    subject = "Your Phantom company profile is live"
    body = (
        f"Good news — Phantom has approved {company_name}'s public profile. "
        f"It's now visible to candidates:\n\n{profile_url}"
    )
    return subject, body


def build_profile_rejected_email(*, company_name: str, reason: str | None) -> tuple[str, str]:
    subject = "Your Phantom company profile needs changes"
    reason_line = f"\n\nReason: {reason}" if reason else ""
    body = (
        f"We're unable to approve {company_name}'s public profile as submitted."
        f"{reason_line}\n\nMake the requested changes and submit it for review again."
    )
    return subject, body


def build_job_alert_email(*, job_title: str, alert_names: list[str]) -> tuple[str, str]:
    subject = f"New match for your job alert: {job_title}"
    matched = ", ".join(alert_names)
    body = (
        f"A new role just went live that matches your saved search ({matched}):\n\n{job_title}\n\n"
        "Open the Shadow job board to view it and apply with your Phantom Passport."
    )
    return subject, body


def build_talent_pool_match_email(*, company_name: str, job_url: str) -> tuple[str, str]:
    # Deliberately no AI-generated content (tier/summary/strengths) in the email itself -- that
    # stays behind login, same privacy-conscious choice as every other AI output in this
    # codebase. This just says a match exists and links back into the app.
    subject = "You've been matched to a potential opportunity"
    body = (
        f"{company_name}, a company you're in a Talent Pool relationship with, found you as a "
        "potential match for a new role.\n\n"
        f"Log in to see the details and decide whether to apply:\n{job_url}"
    )
    return subject, body


def build_new_message_email(*, company_name: str, message_url: str) -> tuple[str, str]:
    # Deliberately no message content in the email itself -- same reasoning as every other
    # notification in this module, the body stays behind login.
    subject = f"New message from {company_name}"
    body = (
        f"{company_name} sent you a new message on Phantom about your application.\n\n"
        f"Read and reply:\n{message_url}"
    )
    return subject, body


def build_reveal_request_email(*, company_name: str, application_url: str) -> tuple[str, str]:
    subject = f"{company_name} has requested to reveal your identity"
    body = (
        f"{company_name} would like to reveal your identity for the role you applied to.\n\n"
        f"Review the request and decide whether to approve it:\n{application_url}"
    )
    return subject, body


def build_talent_pool_request_email(
    *, company_name: str, role_title: str, requests_url: str
) -> tuple[str, str]:
    subject = f"{company_name} would like to keep you on file"
    body = (
        f"{company_name} came across your profile (in connection with {role_title}) and would "
        "like your permission to keep you on file for future roles.\n\n"
        f"Review the request and decide whether to allow it:\n{requests_url}"
    )
    return subject, body


def build_interview_scheduled_email(
    *, company_name: str, scheduled_at_display: str, interviews_url: str
) -> tuple[str, str]:
    subject = f"Interview scheduled with {company_name}"
    body = (
        f"{company_name} has scheduled an interview with you for {scheduled_at_display}.\n\n"
        f"View the details:\n{interviews_url}"
    )
    return subject, body


def build_added_to_pipeline_email(
    *, company_name: str, role_title: str, applications_url: str
) -> tuple[str, str]:
    subject = f"{company_name} added you to consideration for {role_title}"
    body = (
        f"Based on your Talent Pool permission with {company_name}, they've added you to "
        f"consideration for {role_title}. You can review or withdraw the application anytime.\n\n"
        f"View it here:\n{applications_url}"
    )
    return subject, body

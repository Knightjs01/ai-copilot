import html
import logging
import re
from typing import Protocol

import httpx

logger = logging.getLogger("app.auth.email")

_BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Same lockup as the real marketing nav header (frontend/src/components/marketing/marketing-nav
# .tsx) -- served by the app's own custom domain now that one is mapped to the frontend service.
_LOGO_URL = "https://app.phantomhire.io/phantom-hire-logo-new.png"
_GHOST_MARK_URL = "https://app.phantomhire.io/phantom-ghost-mark-email.png"

# Signature-only assets -- cropped directly from the approved "Final Phantom Hire Signature.png"
# design file (not redrawn) so the rendered card is pixel-faithful to it, then served from the
# frontend's own static assets like every other signature image. See _SIGNATURE_HTML below.
_SIGNATURE_AVATAR_URL = "https://app.phantomhire.io/phantom-signature-avatar.png"
_SIGNATURE_SHIP_URL = "https://app.phantomhire.io/phantom-signature-ship.png"
_SIGNATURE_GHOST_MARK_URL = "https://app.phantomhire.io/phantom-signature-ghost-mark.png"
_SIGNATURE_CHECK_URL = "https://app.phantomhire.io/phantom-signature-verified-check.png"
_SIGNATURE_PIN_URL = "https://app.phantomhire.io/phantom-signature-pin.png"
_SIGNATURE_SPARKLE_URL = "https://app.phantomhire.io/phantom-signature-sparkle.png"

# Plain-text fallback only (textContent) -- the styled HTML version lives in _SIGNOFF_HTML below.
# Appended once, centrally, by BrevoEmailSender.send() -- individual build_*_email functions never
# include it themselves, so there's exactly one place that composes the closing + signature.
_SIGN_OFF = "\n\nRegards from the shadows,\nCasper"

_URL_PATTERN = re.compile(r"https?://\S+")

_SIGNOFF_HTML = (
    '<div style="margin:26px 0 22px;font-size:14.5px;line-height:1.6;color:#1a1a2e;">'
    '<span style="display:block;color:#5b5b78;font-style:italic;">Regards from the shadows,</span>'
    '<span style="display:block;font-weight:600;margin-top:2px;">Casper</span>'
    "</div>"
)

# Matches the approved dark/gold "Final Phantom Hire Signature.png" design exactly -- name,
# verified badge, role, location, tagline -- rather than the earlier light/cream card. Kept as
# plain constants rather than generated at send time: this rarely changes, and there's no live
# data source to fetch it from. The avatar/ship/ghost-mark/icon images are direct crops of that
# design file (see the URL constants above), not redrawn, so the rendered card is pixel-faithful
# to the approved artwork.
_SIGNATURE_NAME = "Casper"
_SIGNATURE_TITLE = "Head of Mischief,"
_SIGNATURE_COMPANY = "Phantom Hire"
_SIGNATURE_LOCATION = "London"
_SIGNATURE_TAGLINE_LEAD = "Don't miss the Ghost Ship,"
_SIGNATURE_TAGLINE_LINK = "join Phantom Hire today"
_SIGNATURE_TAGLINE_2_LEAD = "The"
_SIGNATURE_TAGLINE_2_HIGHLIGHT = "Anonymous,"
_SIGNATURE_TAGLINE_2_TAIL = "Private Talent Marketplace"
_SIGNATURE_SITE_URL = "https://app.phantomhire.io"

# Palette sampled directly from the approved design file -- near-black card, soft gold
# verification, near-white body text. Border deliberately muted to gray rather than the sampled
# violet: a full-saturation purple outline competed visually with the purple text accents inside
# the card, making the whole thing harder to scan at a glance (flagged directly by the user after
# seeing it live).
_SIG_BG = "#00030f"
_SIG_BORDER = "#3a3a44"
_SIG_PURPLE = "#8a58f0"
_SIG_GOLD = "#e3c687"
_SIG_WHITE = "#ffffff"
_SIG_SOFT = "#c9c9dc"
_SIG_DIVIDER = "#2f2354"

_SIGNATURE_HTML = (
    f'<table role="presentation" style="margin-top:4px;border-collapse:separate;width:100%;'
    f'max-width:520px;border:1.5px solid {_SIG_BORDER};border-radius:16px;background:{_SIG_BG};">'
    '<tr><td style="padding:20px 22px;">'
    # --- header: avatar, name + verified badge, role, location, small ghost mark -------------
    '<table role="presentation" style="border-collapse:collapse;width:100%;"><tr>'
    '<td style="width:58px;padding-right:14px;vertical-align:top;">'
    f'<a href="{_SIGNATURE_SITE_URL}">'
    f'<img src="{_SIGNATURE_AVATAR_URL}" alt="{_SIGNATURE_NAME}" width="52" height="52" '
    'style="display:block;border-radius:50%;" /></a></td>'
    '<td style="vertical-align:top;font-size:13px;line-height:1.6;">'
    f'<span style="color:{_SIG_WHITE};font-weight:700;font-size:17px;">{_SIGNATURE_NAME}</span> '
    f'<span style="display:inline-block;vertical-align:middle;border:1px solid {_SIG_GOLD};'
    'border-radius:20px;padding:2px 10px 2px 6px;">'
    f'<img src="{_SIGNATURE_CHECK_URL}" alt="" width="11" '
    'style="vertical-align:middle;margin-right:4px;" />'
    f'<span style="color:{_SIG_GOLD};font-size:9px;font-weight:700;letter-spacing:0.06em;'
    f'vertical-align:middle;">VERIFIED</span></span>'
    f'<div style="margin-top:5px;">'
    f'<span style="color:{_SIG_PURPLE};font-weight:700;">{_SIGNATURE_TITLE}</span> '
    f'<span style="color:{_SIG_WHITE};">{_SIGNATURE_COMPANY}</span></div>'
    f'<div style="margin-top:4px;color:{_SIG_SOFT};">'
    f'<img src="{_SIGNATURE_PIN_URL}" alt="" width="9" style="vertical-align:middle;margin-right:5px;" />'
    f"{_SIGNATURE_LOCATION}</div>"
    "</td>"
    '<td style="width:26px;vertical-align:top;text-align:right;">'
    f'<a href="{_SIGNATURE_SITE_URL}"><img src="{_SIGNATURE_GHOST_MARK_URL}" alt="" width="22" '
    'style="display:inline-block;" /></a></td>'
    "</tr></table>"
    # --- divider ------------------------------------------------------------------------------
    f'<div style="margin:16px 0;border-top:1px solid {_SIG_DIVIDER};"></div>'
    # --- footer: ship icon + two taglines, separated by a vertical then horizontal divider ----
    '<table role="presentation" style="border-collapse:collapse;width:100%;"><tr>'
    '<td style="width:46px;vertical-align:top;">'
    f'<a href="{_SIGNATURE_SITE_URL}"><img src="{_SIGNATURE_SHIP_URL}" alt="" width="46" height="46" '
    'style="display:block;border-radius:50%;" /></a></td>'
    f'<td style="width:15px;padding:0 14px;border-left:1px solid {_SIG_DIVIDER};"></td>'
    '<td style="vertical-align:top;font-size:13px;line-height:1.5;">'
    f'<div style="padding-bottom:10px;border-bottom:1px solid {_SIG_DIVIDER};">'
    f'<img src="{_SIGNATURE_SPARKLE_URL}" alt="" width="12" style="vertical-align:middle;margin-right:7px;" />'
    f'<a href="{_SIGNATURE_SITE_URL}" style="text-decoration:none;">'
    f'<span style="color:{_SIG_WHITE};font-weight:700;">{_SIGNATURE_TAGLINE_LEAD}</span> '
    f'<span style="color:{_SIG_PURPLE};font-weight:700;">{_SIGNATURE_TAGLINE_LINK}</span></a></div>'
    '<div style="padding-top:10px;">'
    f'<img src="{_SIGNATURE_SPARKLE_URL}" alt="" width="12" style="vertical-align:middle;margin-right:7px;" />'
    f'<span style="color:{_SIG_WHITE};">{_SIGNATURE_TAGLINE_2_LEAD} '
    f'<span style="color:{_SIG_PURPLE};font-weight:600;">{_SIGNATURE_TAGLINE_2_HIGHLIGHT}</span> '
    f"{_SIGNATURE_TAGLINE_2_TAIL}</span></div>"
    "</td>"
    "</tr></table>"
    "</td></tr></table>"
)


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


def _plain_text_to_html(body: str) -> str:
    """Turns a plain-text email body (paragraphs separated by a blank line, single newlines
    within a paragraph) into simple, inline-styled HTML. Escapes first, then linkifies -- an
    escaped '&' inside a query string is still valid, correctly-decoded text inside an href, so
    doing it in this order is safe, not just convenient. Escaping matters here specifically
    because several callers below (build_workspace_rejected_email's reason, build_info_requested_
    email's message, etc.) embed free text a company reviewer typed themselves -- without this,
    that text would be interpreted as raw HTML inside the sent email."""

    escaped = html.escape(body)
    linked = _URL_PATTERN.sub(
        lambda m: f'<a href="{m.group(0)}" style="color:#5b3df5;">{m.group(0)}</a>', escaped
    )
    paragraphs = [p for p in linked.split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 16px;line-height:1.5;'>{p.replace(chr(10), '<br>')}</p>"
        for p in paragraphs
    )


def _wrap_html(body: str) -> str:
    return (
        "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,"
        "sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;color:#1a1a2e;\">"
        f"<img src=\"{_LOGO_URL}\" alt=\"Phantom Hire\" style=\"height:28px;margin-bottom:28px;\" />"
        f"{_plain_text_to_html(body)}"
        f"{_SIGNOFF_HTML}"
        f"{_SIGNATURE_HTML}"
        "<hr style=\"border:none;border-top:1px solid #e5e5ef;margin:32px 0 16px;\" />"
        "<p style=\"margin:0;font-size:12px;color:#8b8ba7;\">"
        "Phantom Hire · This is an automated message — please don't reply directly to this email."
        "</p></div>"
    )


class BrevoEmailSender:
    """Real EmailSender implementation, backed by Brevo's transactional email API. sender_email
    must already be a verified sender/domain in the Brevo account — Brevo rejects sends from
    unverified senders.

    proxy_url routes the request through a static-IP proxy (e.g. QuotaGuardStatic) so Brevo's
    account-level "Authorized IPs" restriction can stay on and pointed at one fixed IP, instead of
    Railway's outbound IP (which isn't static and can change on redeploy, breaking every send at
    once until someone manually re-approves it in Brevo). None means connect directly."""

    def __init__(
        self,
        *,
        api_key: str,
        sender_email: str,
        sender_name: str = "Casper @ Phantom Hire",
        proxy_url: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._sender_email = sender_email
        self._sender_name = sender_name
        self._proxy_url = proxy_url or None

    async def send(self, *, to: str, subject: str, body: str) -> None:
        async with httpx.AsyncClient(timeout=10.0, proxy=self._proxy_url) as client:
            response = await client.post(
                _BREVO_API_URL,
                headers={
                    "api-key": self._api_key,
                    "content-type": "application/json",
                    "accept": "application/json",
                },
                json={
                    "sender": {"name": self._sender_name, "email": self._sender_email},
                    "to": [{"email": to}],
                    "subject": subject,
                    "htmlContent": _wrap_html(body),
                    "textContent": f"{body}{_SIGN_OFF}",
                },
            )
        if response.status_code >= 300:
            raise EmailSendError(
                f"Brevo rejected the email to {to!r}: {response.status_code} {response.text}"
            )


def build_verification_email(*, verify_url: str) -> tuple[str, str]:
    subject = "Verify your Phantom Hire email"
    body = (
        "Welcome to Phantom Hire! Please confirm your email address to finish setting up your "
        f"account:\n\n{verify_url}\n\nThis link expires soon, so it's best to use it right away."
    )
    return subject, body


def build_password_reset_email(*, reset_url: str) -> tuple[str, str]:
    subject = "Reset your Phantom Hire password"
    body = (
        "We received a request to reset your Phantom Hire password. Choose a new one here:\n\n"
        f"{reset_url}\n\nIf you didn't request this, you can safely ignore this email — your "
        "password won't be changed."
    )
    return subject, body


def build_invite_email(*, company_name: str, accept_url: str) -> tuple[str, str]:
    subject = f"You've been invited to join {company_name} on Phantom Hire"
    body = (
        f"You've been invited to join {company_name}'s workspace on Phantom Hire. Accept your "
        f"invite to set up your account and get started:\n\n{accept_url}"
    )
    return subject, body


def build_workspace_approved_email(*, company_name: str) -> tuple[str, str]:
    subject = "Your Phantom Hire workspace is ready"
    body = (
        f"Good news, we've approved {company_name}'s workspace request.\n\n"
        "You can now log in with the email and password you used to request access, and get "
        "started right away."
    )
    return subject, body


def build_workspace_rejected_email(*, company_name: str, reason: str | None) -> tuple[str, str]:
    subject = "An update on your Phantom Hire access request"
    reason_line = f"\n\nReason: {reason}" if reason else ""
    body = (
        f"We're unable to approve a Phantom Hire workspace for {company_name} at this time."
        f"{reason_line}\n\nIf you believe this is a mistake, or have questions, just reply and "
        "let us know."
    )
    return subject, body


def build_info_requested_email(*, company_name: str, message: str) -> tuple[str, str]:
    subject = "We need a bit more information from you"
    body = (
        f"We're reviewing your Phantom Hire access request for {company_name} and need a little "
        f"more information before we can proceed:\n\n{message}\n\nJust reply to this email with "
        "the details, and we'll pick your request back up."
    )
    return subject, body


def build_profile_approved_email(*, company_name: str, profile_url: str) -> tuple[str, str]:
    subject = "Your Phantom Hire company profile is live"
    body = (
        f"Good news, we've approved {company_name}'s public profile, and it's now visible to "
        f"candidates:\n\n{profile_url}"
    )
    return subject, body


def build_profile_rejected_email(*, company_name: str, reason: str | None) -> tuple[str, str]:
    subject = "Your Phantom Hire company profile needs changes"
    reason_line = f"\n\nReason: {reason}" if reason else ""
    body = (
        f"We're unable to approve {company_name}'s public profile as submitted.{reason_line}\n\n"
        "Make the requested changes and submit it for review again whenever you're ready."
    )
    return subject, body


def build_job_alert_email(*, job_title: str, alert_names: list[str]) -> tuple[str, str]:
    subject = f"New match for your job alert: {job_title}"
    matched = ", ".join(alert_names)
    body = (
        f"A new role just went live that matches your saved search ({matched}):\n\n{job_title}\n\n"
        "Open the Shadow job board to take a look and apply with your Phantom Passport."
    )
    return subject, body


def build_talent_pool_match_email(*, company_name: str, job_url: str) -> tuple[str, str]:
    # Deliberately no AI-generated content (tier/summary/strengths) in the email itself -- that
    # stays behind login, same privacy-conscious choice as every other AI output in this
    # codebase. This just says a match exists and links back into the app.
    subject = "You've been matched to a potential opportunity"
    body = (
        f"{company_name}, a company you're in a Talent Pool relationship with, found you as a "
        f"potential match for a new role.\n\nLog in to see the details and decide whether to "
        f"apply:\n{job_url}"
    )
    return subject, body


def build_new_message_email(*, company_name: str, message_url: str) -> tuple[str, str]:
    # Deliberately no message content in the email itself -- same reasoning as every other
    # notification in this module, the body stays behind login.
    subject = f"New message from {company_name}"
    body = (
        f"{company_name} sent you a new message on Phantom Hire about your application.\n\n"
        f"Read and reply here:\n{message_url}"
    )
    return subject, body


def build_reveal_request_email(*, company_name: str, application_url: str) -> tuple[str, str]:
    subject = f"{company_name} has requested to reveal your identity"
    body = (
        f"{company_name} would like to reveal your identity for the role you applied to. This "
        f"is entirely your decision — nothing changes unless you approve it.\n\nReview the "
        f"request here:\n{application_url}"
    )
    return subject, body


def build_reveal_response_email(
    *, callsign: str, approved: bool, applicant_url: str
) -> tuple[str, str]:
    if approved:
        subject = f"{callsign} approved your reveal request"
        body = (
            f"{callsign} has approved your request to reveal their identity.\n\nView the "
            f"details here:\n{applicant_url}"
        )
    else:
        subject = f"{callsign} declined your reveal request"
        body = (
            f"{callsign} has declined your request to reveal their identity.\n\nView the "
            f"applicant here:\n{applicant_url}"
        )
    return subject, body


def build_talent_pool_request_email(
    *, company_name: str, role_title: str, requests_url: str
) -> tuple[str, str]:
    subject = f"{company_name} would like to keep you on file"
    body = (
        f"{company_name} came across your profile (in connection with {role_title}) and would "
        f"like your permission to keep you on file for future roles.\n\nReview the request and "
        f"decide whether to allow it:\n{requests_url}"
    )
    return subject, body


def build_introduction_request_email(
    *, company_name: str, role_title: str, requests_url: str
) -> tuple[str, str]:
    subject = f"{company_name} would like to introduce themselves"
    body = (
        f"{company_name} came across your profile (in connection with {role_title}) and would "
        f"like to start a conversation. Your identity stays private unless you choose to share "
        f"it later.\n\nReview the request and decide whether to accept:\n{requests_url}"
    )
    return subject, body


def build_introduction_response_email(
    *, callsign: str, approved: bool, applicant_url: str
) -> tuple[str, str]:
    if approved:
        subject = f"{callsign} accepted your introduction request"
        body = (
            f"{callsign} has accepted your introduction request and is now in your pipeline for "
            f"this role.\n\nOpen the conversation here:\n{applicant_url}"
        )
    else:
        subject = f"{callsign} declined your introduction request"
        body = (
            f"{callsign} has declined your introduction request.\n\nView your other candidates "
            f"here:\n{applicant_url}"
        )
    return subject, body


def build_interview_scheduled_email(
    *, company_name: str, scheduled_at_display: str, interviews_url: str
) -> tuple[str, str]:
    subject = f"Interview scheduled with {company_name}"
    body = (
        f"{company_name} has scheduled an interview with you for {scheduled_at_display}.\n\n"
        f"View the details here:\n{interviews_url}"
    )
    return subject, body


def build_added_to_pipeline_email(
    *, company_name: str, role_title: str, applications_url: str
) -> tuple[str, str]:
    subject = f"{company_name} added you to consideration for {role_title}"
    body = (
        f"Based on your Talent Pool permission with {company_name}, they've added you to "
        f"consideration for {role_title}. You're always free to review or withdraw your "
        f"application.\n\nView it here:\n{applications_url}"
    )
    return subject, body

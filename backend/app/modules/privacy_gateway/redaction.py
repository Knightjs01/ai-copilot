import re

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Matches common phone formats: optional leading +/country code, then THREE digit groups
# separated by spaces/dots/dashes (e.g. 123-456-7890, (123) 456-7890, +44 20 7946 0958).
# Requiring three groups (not two) is deliberate — a two-group pattern like \d+[\s.-]\d+ would
# false-positive on date ranges in a resume's experience section (e.g. "2020-2023").
_PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}(?:[\s.-]\d{2,4})?"
)

_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|twitter\.com|x\.com)/\S+"
    r"|https?://\S+",
    re.IGNORECASE,
)


def redact_text(*, text: str, known_full_name: str) -> tuple[str, dict[str, int]]:
    """Rule-based PII redaction — no LLM involved (see module __init__ for why). Order matters:
    redact the known name first (before URL/phone patterns might partially consume it), then
    URLs, then emails, then phone numbers (phone last since its pattern is the most permissive
    and most likely to accidentally match fragments left by earlier substitutions)."""

    counts: dict[str, int] = {"name": 0, "url": 0, "email": 0, "phone": 0}

    redacted = text
    if known_full_name.strip():
        name_pattern = re.compile(re.escape(known_full_name.strip()), re.IGNORECASE)
        redacted, name_count = name_pattern.subn("[REDACTED_NAME]", redacted)
        counts["name"] = name_count

    redacted, url_count = _URL_PATTERN.subn("[REDACTED_URL]", redacted)
    counts["url"] = url_count

    redacted, email_count = _EMAIL_PATTERN.subn("[REDACTED_EMAIL]", redacted)
    counts["email"] = email_count

    redacted, phone_count = _PHONE_PATTERN.subn("[REDACTED_PHONE]", redacted)
    counts["phone"] = phone_count

    return redacted, counts

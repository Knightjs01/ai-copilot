import re

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Public alias — privacy_gateway.service extracts a match with this before redact_text() (below)
# replaces it, to seed the Identity Vault's email field.
EMAIL_PATTERN = _EMAIL_PATTERN

# Common US/UK street-type suffixes, used to recognize a street-address line such as
# "42 Baker Street" or "123 Maple St, Apt 4B". This is a best-effort heuristic, not full
# address NER — unusual address formats may slip through.
_STREET_SUFFIXES = (
    r"Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl|"
    r"Circle|Cir|Terrace|Ter|Square|Sq|Crescent|Cres|Close|Gardens|Grove|Parade|Row|Highway|Hwy"
)

_STREET_ADDRESS_PATTERN = re.compile(
    rf"\b\d{{1,5}}[A-Za-z]?\s+(?:[A-Za-z0-9'.-]+\s+){{0,4}}(?:{_STREET_SUFFIXES})\.?\b"
    r"(?:,?\s*(?:Apt|Suite|Ste|Unit|Floor|Fl)\.?\s*#?\s*[A-Za-z0-9-]+)?",
    re.IGNORECASE,
)

# UK postcode, e.g. "NW1 6XE", "M1 1AE", "SW1A 1AA", "B33 8TH".
_UK_POSTCODE_PATTERN = re.compile(r"\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b", re.IGNORECASE)

# US "City, ST 12345" or "City, ST 12345-6789" tail. Case-sensitive on the state code so
# ordinary two-letter words ("in", "or", "at"...) don't get misread as state abbreviations.
_US_CITY_STATE_ZIP_PATTERN = re.compile(
    r"\b(?:[A-Z][a-zA-Z'-]*\s?){1,3},\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b"
)

# Matches common phone formats: optional leading +/country code, then THREE digit groups
# separated by spaces/dots/dashes (e.g. 123-456-7890, (123) 456-7890, +44 20 7946 0958).
# Requiring three groups (not two) is deliberate — a two-group pattern like \d+[\s.-]\d+ would
# false-positive on date ranges in a resume's experience section (e.g. "2020-2023").
_PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}(?:[\s.-]\d{2,4})?"
)
# Public alias — same extraction-before-redaction reasoning as EMAIL_PATTERN above.
PHONE_PATTERN = _PHONE_PATTERN

_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|twitter\.com|x\.com)/\S+"
    r"|https?://\S+",
    re.IGNORECASE,
)

# LinkedIn-specific — extraction-only, used by privacy_gateway.service to populate the Identity
# Vault's linkedin_url field before redaction destroys the match. Kept separate from _URL_PATTERN
# above (which stays generic across linkedin/github/twitter/x for redaction purposes).
LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/\S+", re.IGNORECASE
)


def _build_name_pattern(full_name: str) -> re.Pattern[str] | None:
    """Matches the full name as one unit AND each individual name part (first, middle, last) as
    a standalone word — resume prose very commonly refers back to a candidate by first name alone
    ("Jonathan is a backend engineer with...") after introducing them by full name once at the
    top, and a full-name-only pattern lets every one of those mentions straight through. Parts
    shorter than 2 characters (initials like "A.") are skipped — matching those would redact
    essentially every short word in the document. Alternatives are ordered longest-first so a
    contiguous "Jonathan Smith" collapses into one match rather than two adjacent ones. This is
    still best-effort, not name NER — nicknames/diminutives ("Jon" for "Jonathan") that never
    appear as an exact substring of the stored name are not caught."""

    full_name = full_name.strip()
    if not full_name:
        return None
    parts = [p for p in re.split(r"\s+", full_name) if len(p) >= 2]
    if not parts:
        return None
    alternatives = sorted({full_name, *parts}, key=len, reverse=True)
    pattern = "|".join(rf"\b{re.escape(p)}\b" for p in alternatives)
    return re.compile(pattern, re.IGNORECASE)


def redact_text(*, text: str, known_full_name: str) -> tuple[str, dict[str, int]]:
    """Rule-based PII redaction — no LLM involved (see module __init__ for why). Order matters:
    the structured, high-confidence patterns (address, URL, email, phone) run first so each gets
    first claim on its own format, then the name pattern runs last as a catch-all sweep over
    whatever's left. Name has to go last now that it also matches individual name parts (see
    _build_name_pattern) — a first/last name is very often a literal substring of the candidate's
    own email (firstname.lastname@...) or street name (e.g. "15 Smith Street"), and redacting the
    name first would consume that substring, leaving the structured pattern nothing recognizable
    to match against."""

    counts: dict[str, int] = {"name": 0, "address": 0, "url": 0, "email": 0, "phone": 0}

    redacted, street_count = _STREET_ADDRESS_PATTERN.subn("[REDACTED_ADDRESS]", text)
    redacted, city_zip_count = _US_CITY_STATE_ZIP_PATTERN.subn("[REDACTED_ADDRESS]", redacted)
    redacted, postcode_count = _UK_POSTCODE_PATTERN.subn("[REDACTED_ADDRESS]", redacted)
    counts["address"] = street_count + city_zip_count + postcode_count

    redacted, url_count = _URL_PATTERN.subn("[REDACTED_URL]", redacted)
    counts["url"] = url_count

    redacted, email_count = _EMAIL_PATTERN.subn("[REDACTED_EMAIL]", redacted)
    counts["email"] = email_count

    redacted, phone_count = _PHONE_PATTERN.subn("[REDACTED_PHONE]", redacted)
    counts["phone"] = phone_count

    name_pattern = _build_name_pattern(known_full_name)
    if name_pattern is not None:
        redacted, name_count = name_pattern.subn("[REDACTED_NAME]", redacted)
        counts["name"] = name_count

    return redacted, counts

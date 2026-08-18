import enum


class DisclosureLevel(str, enum.Enum):
    """Shared between identity_vault (company-Owner-initiated reveal) and shadow_reveal
    (candidate-consented reveal) — previously both were binary: either the full PII snapshot or
    nothing. A recruiter checking basic fit doesn't need a candidate's phone number, and a
    candidate approving a reveal request shouldn't have to hand over their current employer just
    to confirm interest. Each level is a strict superset of the one before it."""

    BASIC = "basic"  # name + location (identity_vault) / name only (shadow_reveal)
    CONTACT = "contact"  # + email, phone
    FULL = "full"  # + employer/title/salary/linkedin (identity_vault) or career history (shadow_reveal)
    # Storage-only sentinel — never a valid input default, only ever written by a reveal service
    # when the caller supplies an explicit per-field selection instead of a tier.
    CUSTOM = "custom"


class IdentityField(str, enum.Enum):
    """The exact set of fields a company Owner can choose to reveal from a candidate's Identity
    Vault. Mirrors app.modules.identity_vault.models.CandidateIdentityVault's real columns."""

    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    LOCATION = "location"
    CURRENT_EMPLOYER = "current_employer"
    CURRENT_TITLE = "current_title"
    LINKEDIN_URL = "linkedin_url"
    EXPECTED_SALARY = "expected_salary"


class ShadowField(str, enum.Enum):
    """The exact set of fields a candidate can choose to disclose when approving a Shadow reveal
    request. Career history stays all-or-nothing as one field, not per-entry."""

    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    CAREER_HISTORY = "career_history"


# Backward-compat tier -> field-set maps. `full_name` (+ `location` for identity_vault) stay
# unconditional within every tier here, reproducing today's reveal_identity/_build_disclosure
# output byte-for-byte when no explicit field selection is given — the "candidate can withhold
# their own name" capability is reached only through an explicit disclosed_fields list, never a
# silent tier-default change.
IDENTITY_TIER_FIELDS: dict[DisclosureLevel, frozenset[IdentityField]] = {
    DisclosureLevel.BASIC: frozenset({IdentityField.FULL_NAME, IdentityField.LOCATION}),
    DisclosureLevel.CONTACT: frozenset(
        {
            IdentityField.FULL_NAME,
            IdentityField.LOCATION,
            IdentityField.EMAIL,
            IdentityField.PHONE,
        }
    ),
    DisclosureLevel.FULL: frozenset(IdentityField),
}

SHADOW_TIER_FIELDS: dict[DisclosureLevel, frozenset[ShadowField]] = {
    DisclosureLevel.BASIC: frozenset({ShadowField.FULL_NAME}),
    DisclosureLevel.CONTACT: frozenset(
        {ShadowField.FULL_NAME, ShadowField.EMAIL, ShadowField.PHONE}
    ),
    DisclosureLevel.FULL: frozenset(ShadowField),
}

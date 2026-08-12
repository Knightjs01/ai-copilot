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

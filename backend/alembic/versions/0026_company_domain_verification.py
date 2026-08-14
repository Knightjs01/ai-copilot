"""Security: basic company domain verification gate — see
app/modules/companies/domain_verification.py. Backfills existing companies from their Owner's
email domain.

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels = None
depends_on = None

# Kept in sync by hand with app/modules/companies/domain_verification.py's _FREE_EMAIL_DOMAINS —
# this is only used for the one-time backfill of pre-existing rows below.
_FREE_EMAIL_DOMAINS = (
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.uk",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "mail.com",
    "gmx.com",
    "gmx.net",
    "yandex.com",
    "yandex.ru",
    "zoho.com",
    "fastmail.com",
    "tutanota.com",
    "qq.com",
    "163.com",
    "126.com",
)


def upgrade() -> None:
    op.add_column(
        "companies", sa.Column("email_domain", sa.String(255), nullable=False, server_default="")
    )
    op.add_column(
        "companies",
        sa.Column("is_verified_domain", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Backfill from each company's Owner — the earliest-created Owner if somehow more than one.
    free_domains_sql = ", ".join(f"'{d}'" for d in _FREE_EMAIL_DOMAINS)
    op.execute(
        f"""
        UPDATE companies c
        SET email_domain = owner.domain,
            is_verified_domain = owner.domain NOT IN ({free_domains_sql})
        FROM (
            SELECT DISTINCT ON (r.company_id)
                r.company_id,
                lower(split_part(u.email, '@', 2)) AS domain
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id AND r.name = 'Owner'
            ORDER BY r.company_id, u.created_at ASC
        ) AS owner
        WHERE owner.company_id = c.id
        """
    )


def downgrade() -> None:
    op.drop_column("companies", "is_verified_domain")
    op.drop_column("companies", "email_domain")

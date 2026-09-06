"""Phantom Hire Phase 7 (Revenue Command, Part 1): real Stripe billing.

New company_billing table -- 1:1 with companies, mirrors company_profile_versions' own shape
(0043_company_profile_review.py): no RLS (companies-adjacent tables aren't tenant-isolated the
way per-tenant data is), dual GRANT to app_runtime and app_auth. Also adds 3 nullable Stripe ID
columns to commercial_plans, populated by a real Stripe API call at sync time (billing.service's
ensure_plans_synced_to_stripe), never migration data -- no migration in this codebase makes
network calls.

Revision ID: 0075
Revises: 0074
Create Date: 2026-09-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0075"
down_revision: str | None = "0074"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_billing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("billing_period", sa.String(20), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_company_billing_company_id", "company_billing", ["company_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON company_billing TO app_runtime, app_auth")

    op.add_column(
        "commercial_plans", sa.Column("stripe_product_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "commercial_plans", sa.Column("stripe_price_id_monthly", sa.String(255), nullable=True)
    )
    op.add_column(
        "commercial_plans", sa.Column("stripe_price_id_annual", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("commercial_plans", "stripe_price_id_annual")
    op.drop_column("commercial_plans", "stripe_price_id_monthly")
    op.drop_column("commercial_plans", "stripe_product_id")

    op.drop_index("ix_company_billing_company_id", table_name="company_billing")
    op.drop_table("company_billing")

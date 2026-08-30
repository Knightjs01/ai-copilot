"""Update Core and Scale plan prices (Growth unchanged) -- Core £299/£2,990 -> £349/£3,490,
Scale £999/£9,990 -> £899/£8,990. Requested directly by the business, not tied to any other
schema change. See 0062_commercial_plans.py for the original seed this updates.

Revision ID: 0066
Revises: 0065
Create Date: 2026-08-30

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0066"
down_revision: str | None = "0065"
branch_labels = None
depends_on = None

_OLD_PRICES = {
    "core": {"monthly": 29900, "annual": 299000},
    "scale": {"monthly": 99900, "annual": 999000},
}
_NEW_PRICES = {
    "core": {"monthly": 34900, "annual": 349000},
    "scale": {"monthly": 89900, "annual": 899000},
}


def _apply(prices: dict[str, dict[str, int]]) -> None:
    plans_table = sa.table(
        "commercial_plans",
        sa.column("code", sa.String),
        sa.column("monthly_price_pence", sa.Integer),
        sa.column("annual_price_pence", sa.Integer),
    )
    for code, price in prices.items():
        op.execute(
            plans_table.update()
            .where(plans_table.c.code == code)
            .values(monthly_price_pence=price["monthly"], annual_price_pence=price["annual"])
        )


def upgrade() -> None:
    _apply(_NEW_PRICES)


def downgrade() -> None:
    _apply(_OLD_PRICES)

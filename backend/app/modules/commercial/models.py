from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class CommercialPlan(UUIDPrimaryKeyMixin, Base):
    """A small, static catalog table -- mirrors platform_admin_permissions' shape (id/code/
    description, no company_id, seeded once by migration). Rows aren't created at runtime; an
    admin picks among the seeded plans (or sets a per-company override) rather than the catalog
    itself ever changing shape via the API. active_role_limit is nullable -- Scale ships with no
    plan default, since its capacity is meant to be negotiated per company via
    Company.active_role_limit_override, not a second fixed number."""

    __tablename__ = "commercial_plans"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    monthly_price_pence: Mapped[int] = mapped_column(Integer)
    annual_price_pence: Mapped[int] = mapped_column(Integer)
    active_role_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

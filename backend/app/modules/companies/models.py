from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Both computed once at signup from the owner's email — see
    # app/modules/companies/domain_verification.py for what "verified" means here (a denylist
    # check, not real domain ownership verification).
    email_domain: Mapped[str] = mapped_column(String(255), default="")
    is_verified_domain: Mapped[bool] = mapped_column(Boolean, default=False)

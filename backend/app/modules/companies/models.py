from typing import Any

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
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

    description: Mapped[str | None] = mapped_column(Text, default=None)
    culture: Mapped[str | None] = mapped_column(Text, default=None)
    benefits: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    size: Mapped[str | None] = mapped_column(String(20), default=None)
    industry: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    # Opted in to having a public /companies/{slug} profile page at all -- default False, same
    # conservative-default convention as PassportVisibility. Job listings always show the
    # company name regardless of this flag (see shadow_jobs/schemas.py's own docstring) -- this
    # only gates the profile *page*, not name visibility on listings.
    is_profile_public: Mapped[bool] = mapped_column(Boolean, default=False)

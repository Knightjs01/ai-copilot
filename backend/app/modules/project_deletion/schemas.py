from datetime import datetime

from pydantic import BaseModel


class PurgeCertificate(BaseModel):
    """Not persisted anywhere — constructed and returned once, at burn time, for the recruiter to
    copy/download. Long-term storage of this (and the reveal audit trail) belongs to the future
    Historic Project Vault, which is a separate, not-yet-built feature."""

    project_title: str
    candidate_count: int
    data_categories_destroyed: list[str]
    purged_at: datetime


class BurnProjectResponse(BaseModel):
    candidate_count: int
    certificate: PurgeCertificate

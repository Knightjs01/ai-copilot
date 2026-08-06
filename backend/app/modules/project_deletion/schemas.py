from datetime import datetime

from pydantic import BaseModel


class PurgeCertificate(BaseModel):
    """Returned once, at burn time, for the recruiter to copy/download. A durable copy is also
    written to historic_vault.PurgedProjectRecord in the same request (see
    ProjectDeletionService.burn_project) so it remains visible in the Historic Project Vault
    long after this response is gone."""

    project_title: str
    candidate_count: int
    data_categories_destroyed: list[str]
    purged_at: datetime


class BurnProjectResponse(BaseModel):
    candidate_count: int
    certificate: PurgeCertificate

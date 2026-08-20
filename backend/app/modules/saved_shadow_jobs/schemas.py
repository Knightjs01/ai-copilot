import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.shadow_jobs.schemas import ShadowJobBoardListing


class SavedShadowJobCreate(BaseModel):
    shadow_job_id: uuid.UUID
    collection_name: str | None = Field(default=None, max_length=100)


class SavedShadowJobUpdate(BaseModel):
    collection_name: str | None = Field(default=None, max_length=100)


class SavedShadowJobRead(BaseModel):
    id: uuid.UUID
    collection_name: str | None
    created_at: datetime
    job: ShadowJobBoardListing

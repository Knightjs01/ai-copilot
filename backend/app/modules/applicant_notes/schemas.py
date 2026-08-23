import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApplicantNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ApplicantNoteRead(BaseModel):
    id: uuid.UUID
    author_user_id: uuid.UUID
    author_email: str
    body: str
    created_at: datetime

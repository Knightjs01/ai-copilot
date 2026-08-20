import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SenderType = Literal["company", "candidate"]


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: uuid.UUID
    sender_type: SenderType
    sender_label: str
    body: str
    created_at: datetime
    is_mine: bool


class MessageThreadRead(BaseModel):
    application_id: uuid.UUID
    messages: list[MessageRead]


class MessageThreadSummary(BaseModel):
    application_id: uuid.UUID
    job_title: str
    company_name: str
    callsign: str
    last_message_preview: str | None
    last_message_at: datetime | None
    unread_count: int

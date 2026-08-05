import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SanitizedProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    redacted_text: str
    redaction_counts: dict[str, int]
    source_file_type: str
    processed_at: datetime

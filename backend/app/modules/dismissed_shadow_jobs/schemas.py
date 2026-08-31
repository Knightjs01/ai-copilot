import uuid

from pydantic import BaseModel


class DismissedShadowJobCreate(BaseModel):
    shadow_job_id: uuid.UUID

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.models import ProjectStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    hiring_manager_id: uuid.UUID | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    role_brief: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = None
    hiring_manager_id: uuid.UUID | None = None
    status: ProjectStatus | None = None
    role_brief: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    department: str | None
    status: ProjectStatus
    hiring_manager_id: uuid.UUID | None
    created_by_id: uuid.UUID
    role_brief: str | None

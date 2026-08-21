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
    # Tri-state (model_fields_set-driven, see api.py::update_project) rather than the plain
    # "if not None" treatment department/role_brief get -- these are LLM-suggested-then-
    # user-edited values, where "clear a wrong AI guess" is a real, expected action.
    seniority: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=255)
    salary_min: int | None = None
    salary_max: int | None = None


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
    seniority: str | None
    location: str | None
    salary_min: int | None
    salary_max: int | None


class JdUploadResult(BaseModel):
    """A preview only -- nothing here is persisted until saved via PATCH /projects/{id}. See
    phantom_passport.schemas.CvParseResult for the identical convention this mirrors."""

    role_brief: str
    seniority: str | None
    location: str | None
    salary_min: int | None
    salary_max: int | None


class ProjectMemberCreate(BaseModel):
    user_id: uuid.UUID


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID

import uuid

from pydantic import BaseModel


class ActionItem(BaseModel):
    type: str
    message: str
    # Nullable -- a reveal-response item's underlying Shadow Job may not be linked to a project.
    project_id: uuid.UUID | None
    project_title: str | None
    candidate_id: uuid.UUID | None
    candidate_callsign: str | None
    # Only set for Shadow-applicant items (reveal-response review, arrange-interview) -- the
    # shadow_job_id + application_id needed to link straight to the real applicant card, which
    # has no ATS Candidate/project route equivalent.
    shadow_job_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None


class DashboardStats(BaseModel):
    live_projects: int
    candidates_in_process: int
    prescreen_stage_count: int
    hiring_manager_stage_count: int
    action_item_count: int
    action_items: list[ActionItem]

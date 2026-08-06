import uuid

from pydantic import BaseModel


class ActionItem(BaseModel):
    type: str
    message: str
    project_id: uuid.UUID
    project_title: str
    candidate_id: uuid.UUID | None
    candidate_callsign: str | None


class DashboardStats(BaseModel):
    live_projects: int
    candidates_in_process: int
    prescreen_stage_count: int
    hiring_manager_stage_count: int
    action_item_count: int
    action_items: list[ActionItem]

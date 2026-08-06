from pydantic import BaseModel


class SalaryStats(BaseModel):
    count: int
    average: float | None
    minimum: int | None
    maximum: int | None


class ProjectAnalytics(BaseModel):
    total_candidates: int
    status_breakdown: dict[str, int]
    prescreen_outcome_breakdown: dict[str, int]
    fit_rating_breakdown: dict[str, int]
    source_breakdown: dict[str, int]
    agency_breakdown: dict[str, int]
    salary_stats: SalaryStats

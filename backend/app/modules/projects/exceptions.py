from app.core.exceptions import AppError


class ProjectError(AppError):
    status_code = 400
    detail = "Project error"


class ProjectNotFoundError(ProjectError):
    status_code = 404
    detail = "Project not found"


class InvalidHiringManagerError(ProjectError):
    status_code = 400
    detail = "Hiring manager must belong to the same company"

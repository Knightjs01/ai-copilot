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


class InvalidProjectMemberError(ProjectError):
    status_code = 400
    detail = "User must belong to the same company"


class UnsupportedJDFileTypeError(ProjectError):
    status_code = 400
    detail = "Unsupported job description file type for automatic text extraction"


class JDExtractionFailedError(ProjectError):
    status_code = 422
    detail = "Could not extract text from this job description file"

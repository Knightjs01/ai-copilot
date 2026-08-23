from app.core.exceptions import AppError


class ApplicantNotesError(AppError):
    status_code = 400
    detail = "Applicant notes error"


class ApplicationNotFoundError(ApplicantNotesError):
    status_code = 404
    detail = "Application not found"

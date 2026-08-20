from app.core.exceptions import AppError


class InterviewsError(AppError):
    status_code = 400
    detail = "Interview scheduling error"


class ApplicationNotFoundError(InterviewsError):
    status_code = 404
    detail = "Application not found"


class InterviewNotFoundError(InterviewsError):
    status_code = 404
    detail = "Interview not found"


class InvalidScheduleTimeError(InterviewsError):
    status_code = 400
    detail = "Interview time must be in the future"

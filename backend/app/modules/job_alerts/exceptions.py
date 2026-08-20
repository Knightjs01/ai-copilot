from app.core.exceptions import AppError


class JobAlertError(AppError):
    status_code = 400
    detail = "Job alert error"


class JobAlertNotFoundError(JobAlertError):
    status_code = 404
    detail = "Job alert not found"


class EmptyAlertCriteriaError(JobAlertError):
    status_code = 400
    detail = "Choose at least one filter for your alert"


class AlertLimitExceededError(JobAlertError):
    status_code = 400
    detail = "You've reached the maximum number of job alerts"

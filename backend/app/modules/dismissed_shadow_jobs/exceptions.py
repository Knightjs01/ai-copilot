from app.core.exceptions import AppError


class DismissedShadowJobError(AppError):
    status_code = 400
    detail = "Dismissed jobs error"


class JobAlreadyDismissedError(DismissedShadowJobError):
    status_code = 409
    detail = "You've already dismissed this job"


class DismissedJobNotFoundError(DismissedShadowJobError):
    status_code = 404
    detail = "Dismissed job not found"

from app.core.exceptions import AppError


class SavedShadowJobError(AppError):
    status_code = 400
    detail = "Saved jobs error"


class ShadowJobNotFoundForSaveError(SavedShadowJobError):
    status_code = 404
    detail = "Shadow job not found"


class JobAlreadySavedError(SavedShadowJobError):
    status_code = 409
    detail = "You've already saved this job"


class SavedJobNotFoundError(SavedShadowJobError):
    status_code = 404
    detail = "Saved job not found"

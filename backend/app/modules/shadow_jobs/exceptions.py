from app.core.exceptions import AppError


class ShadowJobError(AppError):
    status_code = 400
    detail = "Shadow job board error"


class ShadowJobNotFoundError(ShadowJobError):
    status_code = 404
    detail = "Shadow job not found"


class ShadowJobNotPublishedError(ShadowJobError):
    status_code = 400
    detail = "This job is not open for applications"


class ShadowApplicationNotFoundError(ShadowJobError):
    status_code = 404
    detail = "Application not found"


class DuplicateApplicationError(ShadowJobError):
    status_code = 409
    detail = "You have already applied to this job"


class PassportRequiredError(ShadowJobError):
    status_code = 400
    detail = "Build your Phantom Passport before applying"


class CallsignGenerationExhaustedError(ShadowJobError):
    status_code = 500
    detail = "Could not generate a unique callsign for this application"


class ApplicationAlreadyWithdrawnError(ShadowJobError):
    status_code = 400
    detail = "This application has already been withdrawn"

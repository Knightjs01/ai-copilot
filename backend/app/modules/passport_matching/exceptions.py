from app.core.exceptions import AppError


class PassportMatchingError(AppError):
    status_code = 400
    detail = "Passport matching error"


class PassportNotApprovedError(PassportMatchingError):
    status_code = 400
    detail = "Build and approve your Phantom Passport to see match scores"


class ShadowJobNotFoundError(PassportMatchingError):
    status_code = 404
    detail = "This role isn't open for applications anymore"


class TooManyJobsRequestedError(PassportMatchingError):
    status_code = 400
    detail = "Too many jobs requested — batch scoring is capped at 24 jobs per call"


class PassportMatchGenerationError(PassportMatchingError):
    status_code = 502
    detail = "Could not compute match scores — the AI provider request failed"


class ApplicationNotFoundError(PassportMatchingError):
    status_code = 404
    detail = "Applicant not found"


class ApplicationHasNoPassportVersionError(PassportMatchingError):
    status_code = 400
    detail = "This application predates Passport versioning and has no snapshot to score"

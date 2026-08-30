from app.core.exceptions import AppError


class ShadowIntroductionError(AppError):
    status_code = 400
    detail = "Introduction request error"


class IntroductionRequestNotFoundError(ShadowIntroductionError):
    status_code = 404
    detail = "Introduction request not found"


class DuplicateIntroductionRequestError(ShadowIntroductionError):
    status_code = 409
    detail = "An introduction request already exists for this candidate and role"


class IntroductionRequestNotPendingError(ShadowIntroductionError):
    status_code = 400
    detail = "This introduction request has already been answered"


class CandidateNoLongerDiscoverableError(ShadowIntroductionError):
    status_code = 400
    detail = "This candidate is no longer discoverable"

from app.core.exceptions import AppError


class ShadowRevealError(AppError):
    status_code = 400
    detail = "Shadow reveal error"


class RevealRequestNotFoundError(ShadowRevealError):
    status_code = 404
    detail = "Reveal request not found"


class DuplicateRevealRequestError(ShadowRevealError):
    status_code = 409
    detail = "A reveal request already exists for this application"


class RevealRequestNotPendingError(ShadowRevealError):
    status_code = 400
    detail = "This reveal request has already been answered"


class RevealNotApprovedError(ShadowRevealError):
    status_code = 400
    detail = "The candidate has not approved a reveal for this application"

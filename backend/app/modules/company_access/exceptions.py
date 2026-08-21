from app.core.exceptions import AppError


class CompanyAccessError(AppError):
    status_code = 400
    detail = "Company access request error"


class FreeEmailDomainError(CompanyAccessError):
    status_code = 400
    detail = (
        "Phantom is designed for verified professional organisations. "
        "Please use your work email to request access."
    )


class ExistingWorkspaceError(CompanyAccessError):
    status_code = 409
    detail = "Your organisation already has a Phantom workspace. Ask your team to invite you."


class DuplicateRequestError(CompanyAccessError):
    status_code = 409
    detail = "A request for this email is already pending review."


class AccessRequestNotFoundError(CompanyAccessError):
    status_code = 404
    detail = "Access request not found"


class RequestAlreadyReviewedError(CompanyAccessError):
    status_code = 409
    detail = "This request has already been reviewed"

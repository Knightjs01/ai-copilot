from app.core.exceptions import AppError


class CompanyError(AppError):
    status_code = 400
    detail = "Company error"


class CompanyNotFoundError(CompanyError):
    status_code = 404
    detail = "Company not found"


class CompanyAlreadyInStatusError(CompanyError):
    status_code = 409
    detail = "Company is already in that status"


class InvalidProfileTransitionError(CompanyError):
    status_code = 409
    detail = "That profile action isn't valid from the current status"


class InvalidMediaFileError(CompanyError):
    status_code = 400
    detail = "Invalid media file"

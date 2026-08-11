from app.core.exceptions import AppError


class PhantomPassportError(AppError):
    status_code = 400
    detail = "Phantom Passport error"


class PassportNotFoundError(PhantomPassportError):
    status_code = 404
    detail = "Phantom Passport not found"


class CvParsingFailedError(PhantomPassportError):
    status_code = 422
    detail = "Could not parse this CV"

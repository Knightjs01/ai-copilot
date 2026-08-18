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


class InvalidCvFileError(PhantomPassportError):
    status_code = 422
    detail = "Invalid CV file"


class OriginalCvNotFoundError(PhantomPassportError):
    status_code = 404
    detail = "No CV is currently stored in your Candidate Vault"


class PassportNotApprovedError(PhantomPassportError):
    status_code = 400
    detail = "Approve your Phantom Passport before applying — nothing is shared until you do"


class CallsignGenerationExhaustedError(PhantomPassportError):
    status_code = 500
    detail = "Could not generate a unique Callsign for this Passport"


class AiSuggestionFailedError(PhantomPassportError):
    status_code = 502
    detail = "Could not generate a suggestion — the AI provider request failed"

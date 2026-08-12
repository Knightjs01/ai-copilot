from app.core.exceptions import AppError


class CandidateAuthError(AppError):
    status_code = 400
    detail = "Authentication error"


class CandidateEmailAlreadyRegisteredError(CandidateAuthError):
    status_code = 409
    detail = "Email is already registered"


class CandidateInvalidCredentialsError(CandidateAuthError):
    status_code = 401
    detail = "Invalid email or password"


class CandidateInvalidOrExpiredTokenError(CandidateAuthError):
    status_code = 401
    detail = "Invalid or expired token"


class CandidateInvalidMfaCodeError(CandidateAuthError):
    status_code = 401
    detail = "Invalid MFA code"


class CandidateSessionNotFoundError(CandidateAuthError):
    status_code = 404
    detail = "Session not found"

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


class CandidateInvalidWebAuthnCredentialError(CandidateAuthError):
    status_code = 401
    detail = "Invalid passkey credential"


class CandidateWebAuthnCredentialNotFoundError(CandidateAuthError):
    status_code = 404
    detail = "Passkey not found"


class CandidateEmailDeliveryError(CandidateAuthError):
    """Raised only for an explicit resend-verification request, which deserves to know it
    failed -- see auth.exceptions.EmailDeliveryError's docstring for why a raw EmailSendError
    must never be allowed to reach the API layer unconverted (it isn't an AppError, so it
    produces a bare 500 the browser reports as "Failed to fetch" instead of a real message)."""

    status_code = 502
    detail = "Couldn't send that email right now. Try again in a moment."

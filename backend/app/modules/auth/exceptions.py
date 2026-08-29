from app.core.exceptions import AppError


class AuthError(AppError):
    status_code = 400
    detail = "Authentication error"


class EmailAlreadyRegisteredError(AuthError):
    status_code = 409
    detail = "Email is already registered"


class InvalidCredentialsError(AuthError):
    status_code = 401
    detail = "Invalid email or password"


class InvalidOrExpiredTokenError(AuthError):
    status_code = 401
    detail = "Invalid or expired token"


class InvalidMfaCodeError(AuthError):
    status_code = 401
    detail = "Invalid MFA code"


class PermissionDeniedError(AuthError):
    status_code = 403
    detail = "You do not have permission to perform this action"


class UserNotFoundError(AuthError):
    status_code = 404
    detail = "User not found"


class LastOwnerError(AuthError):
    status_code = 400
    detail = "A company must always have at least one Owner"


class InvalidRoleError(AuthError):
    status_code = 400
    detail = "Invalid role"


class SessionNotFoundError(AuthError):
    status_code = 404
    detail = "Session not found"


class InvalidWebAuthnCredentialError(AuthError):
    status_code = 401
    detail = "Invalid passkey credential"


class WebAuthnCredentialNotFoundError(AuthError):
    status_code = 404
    detail = "Passkey not found"


class EmailDeliveryError(AuthError):
    """Raised only where the caller explicitly asked for an email and deserves to know it
    failed (a resend-verification click) -- as opposed to signup/provisioning/invite flows,
    which must never fail the primary action over a mail-provider hiccup and instead log a
    warning and let the recipient retry. A raw EmailSendError must never reach this far
    unconverted -- it isn't an AppError, so FastAPI's default handling of it is a bare 500 with
    no guaranteed CORS headers, which the browser reports as a generic "Failed to fetch" instead
    of a real error message."""

    status_code = 502
    detail = "Couldn't send that email right now. Try again in a moment."

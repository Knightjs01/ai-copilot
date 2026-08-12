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

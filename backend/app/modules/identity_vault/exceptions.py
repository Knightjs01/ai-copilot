from app.core.exceptions import AppError


class IdentityVaultError(AppError):
    status_code = 400
    detail = "Identity vault error"


class IdentityVaultNotFoundError(IdentityVaultError):
    status_code = 404
    detail = "No vault record exists for this candidate"


class RevealEventNotFoundError(IdentityVaultError):
    status_code = 404
    detail = "Reveal event not found"


class CallsignGenerationExhaustedError(IdentityVaultError):
    status_code = 500
    detail = "Could not generate a unique callsign — try again"

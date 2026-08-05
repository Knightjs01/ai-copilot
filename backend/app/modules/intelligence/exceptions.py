from app.core.exceptions import AppError


class IntelligenceError(AppError):
    status_code = 400
    detail = "Intelligence pack error"


class IntelligencePackNotFoundError(IntelligenceError):
    status_code = 404
    detail = "No intelligence pack exists for this candidate yet"


class IntelligencePackGenerationError(IntelligenceError):
    status_code = 502
    detail = "Could not generate the intelligence pack — the AI provider request failed"

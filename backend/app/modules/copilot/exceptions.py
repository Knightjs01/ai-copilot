from app.core.exceptions import AppError


class CopilotError(AppError):
    status_code = 400
    detail = "Phantom AI error"


class CopilotGenerationError(CopilotError):
    status_code = 502
    detail = "Phantom AI couldn't generate a response right now"

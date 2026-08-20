from app.core.exceptions import AppError


class MessagesError(AppError):
    status_code = 400
    detail = "Messaging error"


class ApplicationNotFoundError(MessagesError):
    status_code = 404
    detail = "Application not found"

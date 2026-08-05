from app.core.exceptions import AppError


class HiringManagerAlignmentError(AppError):
    status_code = 400
    detail = "Hiring manager alignment error"


class HiringManagerAlignmentNotFoundError(HiringManagerAlignmentError):
    status_code = 404
    detail = "No hiring manager alignment exists for this project yet"

from app.core.exceptions import AppError


class CommercialError(AppError):
    status_code = 400
    detail = "Commercial error"


class CommercialPlanNotFoundError(CommercialError):
    status_code = 404
    detail = "Commercial plan not found"

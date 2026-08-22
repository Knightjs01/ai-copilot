from app.core.exceptions import AppError


class TalentPoolError(AppError):
    status_code = 400
    detail = "Talent Pool error"


class TalentPoolRequestNotFoundError(TalentPoolError):
    status_code = 404
    detail = "Talent Pool request not found"


class DuplicateTalentPoolRequestError(TalentPoolError):
    status_code = 409
    detail = "A Talent Pool request already exists for this candidate and company"


class TalentPoolRequestNotPendingError(TalentPoolError):
    status_code = 400
    detail = "This Talent Pool request has already been answered"


class TalentPoolGrantNotActiveError(TalentPoolError):
    status_code = 400
    detail = "This candidate is not currently in your Talent Pool"


class TalentPoolRequestNotEligibleError(TalentPoolError):
    status_code = 400
    detail = "This role must be closed, or the application declined or withdrawn, before requesting Talent Pool"

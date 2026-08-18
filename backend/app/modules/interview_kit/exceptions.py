from app.core.exceptions import AppError


class InterviewKitError(AppError):
    status_code = 400
    detail = "Interview kit error"


class InterviewKitNotFoundError(InterviewKitError):
    status_code = 404
    detail = "No interview kit exists for this project yet"


class MissingHiringBlueprintError(InterviewKitError):
    status_code = 400
    detail = "This project has no hiring blueprint yet — generate one first"


class InterviewKitGenerationError(InterviewKitError):
    status_code = 502
    detail = "Could not generate the interview kit — the AI provider request failed"

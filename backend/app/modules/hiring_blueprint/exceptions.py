from app.core.exceptions import AppError


class HiringBlueprintError(AppError):
    status_code = 400
    detail = "Hiring blueprint error"


class HiringBlueprintNotFoundError(HiringBlueprintError):
    status_code = 404
    detail = "No hiring blueprint exists for this project yet"


class MissingRoleBriefError(HiringBlueprintError):
    status_code = 400
    detail = "Set a role_brief on this project before generating a hiring blueprint"


class HiringBlueprintGenerationError(HiringBlueprintError):
    status_code = 502
    detail = "Could not generate the hiring blueprint — the AI provider request failed"

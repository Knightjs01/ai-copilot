from app.core.exceptions import AppError


class PrescreenAssessmentError(AppError):
    status_code = 400
    detail = "Pre-screen assessment error"


class PrescreenAssessmentNotFoundError(PrescreenAssessmentError):
    status_code = 404
    detail = "No pre-screen assessment exists for this candidate yet"


class MissingHiringBlueprintError(PrescreenAssessmentError):
    status_code = 400
    detail = "This candidate's project has no hiring blueprint yet — generate one first"


class MissingHiringManagerAlignmentError(PrescreenAssessmentError):
    status_code = 400
    detail = "This candidate's project has no hiring manager alignment yet — submit one first"


class PrescreenNotesRequiredError(PrescreenAssessmentError):
    status_code = 400
    detail = "Record prescreen_notes on this candidate before generating handoff recommendations"


class PrescreenAssessmentGenerationError(PrescreenAssessmentError):
    status_code = 502
    detail = "Could not generate the pre-screen assessment — the AI provider request failed"

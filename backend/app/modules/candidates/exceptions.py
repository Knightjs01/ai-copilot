from app.core.exceptions import AppError


class CandidateError(AppError):
    status_code = 400
    detail = "Candidate error"


class CandidateNotFoundError(CandidateError):
    status_code = 404
    detail = "Candidate not found"


class ResumeNotFoundError(CandidateError):
    status_code = 404
    detail = "No resume has been uploaded for this candidate"


class InvalidResumeFileError(CandidateError):
    status_code = 400
    detail = "Invalid resume file"

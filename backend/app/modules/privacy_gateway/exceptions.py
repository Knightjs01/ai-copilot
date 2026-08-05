from app.core.exceptions import AppError


class PrivacyGatewayError(AppError):
    status_code = 400
    detail = "Privacy gateway error"


class SanitizedProfileNotFoundError(PrivacyGatewayError):
    status_code = 404
    detail = "No sanitized profile exists for this candidate yet"


class UnsupportedFileTypeError(PrivacyGatewayError):
    status_code = 400
    detail = "Unsupported resume file type for automatic text extraction"


class NoResumeUploadedError(PrivacyGatewayError):
    status_code = 400
    detail = "This candidate has no resume uploaded to sanitize"


class ExtractionFailedError(PrivacyGatewayError):
    status_code = 422
    detail = "Could not extract text from this resume file"

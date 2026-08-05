class AppError(Exception):
    """Base for domain exceptions across all modules — carries an HTTP status code and a
    user-facing detail message. One handler in app.main covers every subclass via MRO lookup,
    so new modules just subclass this instead of adding their own exception handler."""

    status_code = 400
    detail = "Application error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail

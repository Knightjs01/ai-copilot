from app.modules.candidates.storage import FileStorage, LocalFileStorage

_default_storage = LocalFileStorage()


def get_file_storage() -> FileStorage:
    """Overridable via app.dependency_overrides — tests inject a temp-directory-backed storage
    instead of writing into the same directory used for local dev, same pattern as
    app.modules.auth.dependencies.get_email_sender."""

    return _default_storage

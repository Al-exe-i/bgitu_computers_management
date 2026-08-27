class AdministrationError(Exception):
    detail = "Administration operation failed"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class ProtectedFileAccessDeniedError(AdministrationError):
    detail = "Access denied"


class ProtectedFileNotFoundError(AdministrationError):
    detail = "File not found"

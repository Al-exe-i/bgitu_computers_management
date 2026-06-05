class InventoryError(Exception):
    detail = "Inventory operation failed"


class AudienceNotFoundError(InventoryError):
    detail = "Audience not found"


class AudienceAlreadyExistsError(InventoryError):
    detail = "Audience already exists in this office"


class AudienceGridValidationError(InventoryError):
    detail = "Audience grid is invalid"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class AudienceHardwareNotFoundError(AudienceGridValidationError):
    def __init__(self, *, hardware_id: int, audience_id: int) -> None:
        super().__init__(f"Hardware id={hardware_id} not found in audience {audience_id}")


class HardwareNotFoundError(InventoryError):
    detail = "Hardware not found"


class HardwarePermissionDeniedError(InventoryError):
    detail = "Hardware operation is not allowed"


class OfficeNotFoundError(InventoryError):
    detail = "Office not found"


class OfficeAlreadyExistsError(InventoryError):
    detail = "Office already exists"


class HardwareFileNotFoundError(InventoryError):
    detail = "File record not found"


class HardwareFileMissingOnDiskError(InventoryError):
    detail = "File missing on disk"


class HardwareFileUnsupportedMediaError(InventoryError):
    detail = "Not a video file"


class HardwareFileBadRangeError(InventoryError):
    detail = "Bad Range header"


class HardwareFileRangeNotSatisfiableError(InventoryError):
    detail = "Range not satisfiable"

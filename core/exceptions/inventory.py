class InventoryError(Exception):
    detail = "Inventory operation failed"


class HardwareNotFoundError(InventoryError):
    detail = "Hardware not found"


class HardwarePermissionDeniedError(InventoryError):
    detail = "Hardware operation is not allowed"


class OfficeNotFoundError(InventoryError):
    detail = "Office not found"


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

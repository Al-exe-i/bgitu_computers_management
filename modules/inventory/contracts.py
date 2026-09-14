from dataclasses import dataclass

from modules.inventory.schemas.hardware_file import HardwareFileResponse


@dataclass(slots=True, frozen=True)
class HardwareFilesUpdateResult:
    files: list[HardwareFileResponse]
    audience_id: int


@dataclass(slots=True, frozen=True)
class HardwareFileDeleteResult:
    audience_id: int

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_INSTALLED_SOFTWARE_ITEMS = 100
MAX_SOFTWARE_NAME_LENGTH = 128
SoftwareName = Annotated[
    str,
    Field(min_length=1, max_length=MAX_SOFTWARE_NAME_LENGTH),
]


class MemoryUnit(str, Enum):
    mb = "mb"
    gb = "gb"
    tb = "tb"


class OperatingSystem(str, Enum):
    windows = "windows"
    macos = "macos"
    linux = "linux"


OPERATING_SYSTEM_EDITIONS: dict[OperatingSystem, tuple[str, ...]] = {
    OperatingSystem.windows: (
        "Windows 11 Home",
        "Windows 11 Pro",
        "Windows 11 Education",
        "Windows 11 Enterprise",
        "Windows 10 Home",
        "Windows 10 Pro",
        "Windows 10 Education",
        "Windows 10 Enterprise",
    ),
    OperatingSystem.macos: (
        "macOS Tahoe",
        "macOS Sequoia",
        "macOS Sonoma",
        "macOS Ventura",
        "macOS Monterey",
    ),
    OperatingSystem.linux: (
        "Ubuntu",
        "Debian",
        "Fedora Workstation",
        "Arch Linux",
        "Astra Linux",
        "ALT Workstation",
        "Linux Mint",
    ),
}


class ComputeSpecsBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu_model: str | None = Field(default=None, max_length=128)
    cpu_frequency_ghz: float | None = Field(default=None, gt=0)
    cpu_cores: int | None = Field(default=None, ge=1)

    ram_amount: int | None = Field(default=None, ge=1)
    ram_unit: MemoryUnit | None = None

    storage_amount: int | None = Field(default=None, ge=1)
    storage_unit: MemoryUnit | None = None

    purchase_year: int | None = Field(default=None, ge=2000, le=2100)


class ComputerSpecs(ComputeSpecsBase):
    operating_system: OperatingSystem | None = None
    os_edition: str | None = Field(default=None, max_length=128)
    installed_software: list[SoftwareName] | None = Field(
        default=None,
        max_length=MAX_INSTALLED_SOFTWARE_ITEMS,
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_operating_system(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        data = dict(value)
        raw_operating_system = data.get("operating_system")
        if not isinstance(raw_operating_system, str):
            return data

        normalized = raw_operating_system.strip()
        normalized_key = normalized.casefold()

        for operating_system in OperatingSystem:
            if normalized_key == operating_system.value:
                data["operating_system"] = operating_system.value
                return data

            for edition in OPERATING_SYSTEM_EDITIONS[operating_system]:
                if normalized_key == edition.casefold():
                    data["operating_system"] = operating_system.value
                    current_edition = data.get("os_edition")
                    if not isinstance(current_edition, str) or not current_edition.strip():
                        data["os_edition"] = edition
                    return data

        return data

    @field_validator("os_edition", mode="before")
    @classmethod
    def normalize_os_edition(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip() or None

    @field_validator("installed_software", mode="before")
    @classmethod
    def normalize_installed_software(cls, value: object) -> object:
        if value is None or not isinstance(value, list):
            return value

        normalized: list[object] = []
        seen: set[str] = set()

        for item in value:
            if not isinstance(item, str):
                normalized.append(item)
                continue

            name = item.strip()
            if not name:
                continue

            deduplication_key = name.casefold()
            if deduplication_key in seen:
                continue

            seen.add(deduplication_key)
            normalized.append(name)

        return normalized or None

    @model_validator(mode="after")
    def validate_os_edition(self) -> "ComputerSpecs":
        if self.os_edition is None:
            return self

        if self.operating_system is None:
            raise ValueError("Operating system must be selected before its edition")

        allowed_editions = OPERATING_SYSTEM_EDITIONS[self.operating_system]
        if self.os_edition not in allowed_editions:
            raise ValueError(
                f"Unsupported edition for {self.operating_system.value}: "
                f"{self.os_edition}"
            )

        return self


class ServerSpecs(ComputeSpecsBase):
    pass


class SwitchSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ports_count: int | None = Field(default=None, ge=1)
    managed: bool | None = None


class EmptySpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

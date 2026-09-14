"""Read-only contracts exposed to other business modules."""
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from modules.inventory.types import HardwareType

__all__ = ["AudienceContext", "AudienceDirectory", "HardwareType", "OfficeContext", "OfficeDirectory"]


@dataclass(frozen=True, slots=True)
class AudienceContext:
    id: int
    public_id: UUID
    number: int
    office_id: int


@dataclass(frozen=True, slots=True)
class OfficeContext:
    id: int
    address: str


class AudienceDirectory(Protocol):
    async def get_one_short(self, audience_id: int) -> AudienceContext | None: ...


class OfficeDirectory(Protocol):
    async def get_one_short(self, office_id: int) -> OfficeContext | None: ...

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class InitialOffice:
    id: int
    address: str


class OfficeProvisioner(Protocol):
    async def ensure_offices(
        self, offices: tuple[InitialOffice, ...]
    ) -> tuple[int, ...]: ...

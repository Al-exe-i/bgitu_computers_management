from collections.abc import Iterator
from dataclasses import dataclass

from modules.identity.public import InitialSuperuser, ManagedUserResult
from modules.inventory.public import InitialOffice


@dataclass(slots=True, frozen=True)
class BootstrapPlan:
    offices: tuple[InitialOffice, ...]
    superuser: InitialSuperuser


@dataclass(slots=True, frozen=True)
class BootstrapResult:
    created_office_ids: tuple[int, ...]
    superuser: ManagedUserResult | None
    superuser_created: bool


@dataclass(slots=True, frozen=True)
class ProtectedFile:
    content: Iterator[bytes]
    filename: str
    media_type: str

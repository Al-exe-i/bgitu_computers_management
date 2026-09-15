from dataclasses import dataclass, field
from typing import Protocol

from modules.identity.roles import UserRole


@dataclass(slots=True, frozen=True)
class ManagedUserResult:
    id: int
    email: str
    role: UserRole
    is_superuser: bool


@dataclass(slots=True, frozen=True)
class InitialSuperuser:
    email: str | None = None
    password: str | None = field(default=None, repr=False)
    name: str | None = None
    surname: str | None = None
    required: bool = True


class InitialUserProvisioner(Protocol):
    async def ensure_initial_superuser(
        self, config: InitialSuperuser
    ) -> tuple[ManagedUserResult | None, bool]: ...

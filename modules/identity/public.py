"""Data-only identity API for other modules; never exports ORM models."""

from typing import Protocol

from modules.identity.contracts import UserSummary
from modules.identity.management_contracts import (
    InitialSuperuser,
    InitialUserProvisioner,
    ManagedUserResult,
)
from modules.identity.management_validation import validate_password
from modules.identity.roles import UserRole
from modules.identity.schemas.user import AuthenticatedUser, UserOut

__all__ = [
    "AuthenticatedUser",
    "UserDirectory",
    "UserOut",
    "UserRole",
    "UserSummary",
    "UserSummaryDirectory",
]
__all__ += ["InitialSuperuser", "InitialUserProvisioner", "ManagedUserResult"]
__all__ += ["validate_password"]


class UserDirectory(Protocol):
    async def exists(self, user_id: int) -> bool: ...


class UserSummaryDirectory(Protocol):
    async def get_summaries(self, user_ids: set[int]) -> dict[int, UserSummary]: ...

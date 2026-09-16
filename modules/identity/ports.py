from collections.abc import Iterator, Sequence
from typing import Protocol

from modules.identity.contracts import (
    LogoutResult,
    RevokeSessionResult,
    TokenIssueResult,
    UserCredentials,
    UserPhotoUpdateResult,
)
from modules.identity.roles import UserRole
from modules.identity.schemas.user import UserCreate, UserOut, UserUpdate
from modules.identity.schemas.user_session import UserSessionOut


class Transaction(Protocol):
    async def commit(self) -> None: ...


class IdentityActor(Protocol):
    id: int
    role: UserRole
    is_superuser: bool
    photo: str | None


class UploadedAvatarFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...
    async def close(self) -> None: ...


class StoredAvatarFile(Protocol):
    media_type: str
    filename: str

    def iter_file(self) -> Iterator[bytes]: ...


class AuthServicePort(Protocol):
    async def login(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenIssueResult: ...

    async def refresh(
        self,
        *,
        refresh_token: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenIssueResult: ...

    async def logout(
        self,
        *,
        refresh_token: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> LogoutResult: ...

    async def logout_all(self, *, user_id: int) -> None: ...

    async def list_user_sessions(
        self,
        *,
        user_id: int,
        include_inactive: bool,
        refresh_token: str | None,
    ) -> list[UserSessionOut]: ...

    async def revoke_session(
        self,
        *,
        user_id: int,
        sid: str,
        refresh_token: str | None,
    ) -> RevokeSessionResult: ...


class UserServicePort(Protocol):
    async def get_all(self) -> Sequence[UserOut]: ...
    async def get(self, user_id: int) -> UserOut | None: ...
    async def get_by_email(self, email: str) -> UserCredentials | None: ...
    async def get_access_token_version(self, user_id: int) -> int | None: ...
    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None: ...
    async def verify_password(self, user_id: int, password: str) -> bool: ...
    async def update_password(self, user_id: int, password: str) -> UserOut | None: ...
    async def create(self, data: UserCreate) -> UserOut | None: ...
    async def delete(self, user_id: int) -> bool: ...
    def get_photo(self, user: IdentityActor) -> StoredAvatarFile | None: ...

    async def upload_photo(
        self,
        user_id: int,
        file: UploadedAvatarFile,
    ) -> UserPhotoUpdateResult | None: ...

    async def delete_photo(self, user_id: int) -> UserPhotoUpdateResult | None: ...

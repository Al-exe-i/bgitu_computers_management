from collections.abc import Iterator, Sequence
from typing import Any, Protocol

from schemas.invite import (
    InviteCreateBatch,
    InviteCreateOne,
    InviteCreateResult,
    InviteListItem,
    InvitePreviewResponse,
)
from schemas.user import UserCreate, UserOut, UserUpdate
from schemas.user_session import UserSessionOut


class AuditLogger(Protocol):
    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ) -> Any: ...


class IdentityActor(Protocol):
    id: int
    role: Any
    is_superuser: bool
    password: str
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


class UserPhotoUpdateResult(Protocol):
    user: UserOut
    had_photo: bool


class TokenIssueResult(Protocol):
    user_id: int
    user_email: str | None
    sid: str
    access_token: str
    refresh_token: str


class LogoutResult(Protocol):
    user_id: int | None
    sid: str | None


class RevokeSessionResult(Protocol):
    revoked_current_session: bool


class InviteRegistrationData(Protocol):
    id: int
    target_email: str | None
    target_role: Any


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
    async def get_all(self) -> Sequence[Any]: ...
    async def get(self, user_id: int) -> Any | None: ...
    async def get_by_email(self, email: str) -> Any | None: ...
    async def get_access_token_version(self, user_id: int) -> int | None: ...
    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None: ...
    async def create(self, data: UserCreate) -> UserOut | None: ...
    async def delete(self, user_id: int) -> bool: ...
    def get_photo(self, user: IdentityActor) -> StoredAvatarFile | None: ...

    async def upload_photo(
        self,
        user_id: int,
        file: UploadedAvatarFile,
    ) -> UserPhotoUpdateResult | None: ...

    async def delete_photo(self, user_id: int) -> UserPhotoUpdateResult | None: ...


class InviteServicePort(Protocol):
    async def preview(self, token: str) -> InvitePreviewResponse: ...

    async def get_active_for_registration(self, token: str) -> InviteRegistrationData: ...

    async def mark_used(self, invite_id: int, *, used_by_user_id: int) -> None: ...

    async def create_one(
        self,
        created_by_user_id: int,
        schema: InviteCreateOne,
    ) -> InviteCreateResult: ...

    async def create_batch(
        self,
        created_by_user_id: int,
        schema: InviteCreateBatch,
    ) -> list[InviteCreateResult]: ...

    async def list_all(self) -> list[InviteListItem]: ...
    async def revoke(self, invite_id: int) -> InviteListItem: ...
    async def delete(self, invite_id: int) -> None: ...

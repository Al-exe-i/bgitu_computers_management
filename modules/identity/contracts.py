from dataclasses import dataclass, field

from modules.identity.schemas.user import UserOut


@dataclass(frozen=True, slots=True)
class UserSummary:
    id: int
    email: str | None
    name: str | None
    surname: str | None


@dataclass(frozen=True, slots=True)
class TokenIssueResult:
    user_id: int
    user_email: str | None
    sid: str
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class LogoutResult:
    user_id: int | None
    sid: str | None


@dataclass(frozen=True, slots=True)
class RevokeSessionResult:
    revoked_current_session: bool


@dataclass(frozen=True, slots=True)
class UserPhotoUpdateResult:
    user: UserOut
    had_photo: bool


@dataclass(frozen=True, slots=True)
class UserCredentials:
    id: int
    email: str
    password: str = field(repr=False)
    access_token_version: int

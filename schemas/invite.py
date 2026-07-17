from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.user import UserRole
from utils.email import RuEmailStr


class InviteCreateOne(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_email: RuEmailStr | None = None
    target_role: UserRole = UserRole.teacher
    expires_at: datetime
    note: str | None = Field(default=None, max_length=255)


class InviteCreateBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int | None = Field(default=None, ge=1, le=200)
    emails: list[RuEmailStr] | None = None
    target_role: UserRole = UserRole.teacher
    expires_at: datetime
    note: str | None = Field(default=None, max_length=255)


class InviteCreateResult(BaseModel):
    id: int
    invite_url: str
    target_email: EmailStr | None = None
    target_role: UserRole
    expires_at: datetime
    note: str | None = None


class InviteListItem(BaseModel):
    id: int
    target_email: EmailStr | None = None
    target_role: UserRole
    note: str | None = None
    created_by_user_id: int
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    used_by_user_id: int | None = None


class InvitePreviewRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class InvitePreviewResponse(BaseModel):
    valid: bool
    target_email: EmailStr | None = None
    target_role: UserRole | None = None
    expires_at: datetime | None = None
    reason: str | None = None


class RegisterByInviteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=256)
    name: str | None = Field(default=None, max_length=64)
    surname: str | None = Field(default=None, max_length=64)
    email: RuEmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterByInviteResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str

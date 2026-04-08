from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from models.user import UserRole


class InviteCreateOne(BaseModel):
    target_email: EmailStr | None = None
    target_role: UserRole = UserRole.teacher
    expires_at: datetime
    note: str | None = None


class InviteCreateBatch(BaseModel):
    count: int | None = Field(default=None, ge=1, le=200)
    emails: list[EmailStr] | None = None
    target_role: UserRole = UserRole.teacher
    expires_at: datetime
    note: str | None = None


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
    token: str


class InvitePreviewResponse(BaseModel):
    valid: bool
    target_email: EmailStr | None = None
    target_role: UserRole | None = None
    expires_at: datetime | None = None
    reason: str | None = None


class RegisterByInviteRequest(BaseModel):
    token: str
    name: str | None = None
    surname: str | None = None
    email: EmailStr
    password: str


class RegisterByInviteResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str
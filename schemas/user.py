from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from models.user import UserRole
from utils.email import RuEmailStr


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=64)
    surname: str | None = Field(default=None, max_length=64)
    role: UserRole


class UserCreate(UserBase):
    email: RuEmailStr
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=64)
    surname: str | None = Field(default=None, max_length=64)
    role: UserRole | None = None


class UserOut(UserBase):
    id: int
    email: str
    photo: str | None = None
    reg_date: datetime
    is_superuser: bool


class ChangePasswordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)

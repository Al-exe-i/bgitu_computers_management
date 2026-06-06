from pydantic import BaseModel, Field
from datetime import datetime

from models.user import UserRole


class UserBase(BaseModel):
    name: str | None = None
    surname: str | None = None
    photo: str | None = None
    role: UserRole


class UserCreate(UserBase):
    email: str  # Потом поменять на EmailStr, если добавлю логин
    password: str = Field(min_length=6)


class UserUpdate(UserBase):
    password: str | None = None
    role: UserRole | None = None


class UserOut(UserBase):
    id: int
    email: str
    reg_date: datetime
    is_superuser: bool

class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)

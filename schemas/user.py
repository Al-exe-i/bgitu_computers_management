from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    name: str | None = None
    surname: str | None = None
    email: str # Потом поменять на EmailStr, если добавлю логин
    telegram_id: str | None = None
    telegram_id_confirmed: bool = Field(default=False)
    photo: str | None = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: str | None = None

class UserOut(UserBase):
    id: int
    reg_date: datetime
    is_superuser: bool

    class Config:
        from_attributes = True  # для SQLAlchemy ORM-моделей (ранее orm_mode=True)
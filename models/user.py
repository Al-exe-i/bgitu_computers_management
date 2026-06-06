from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from sqlalchemy import String, DateTime, func, Integer
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from models.mixins.int_id_pk_mixin import IntIdPkMixin
import enum


class UserRole(enum.Enum):
    admin = 1
    teacher = 2


class User(IntIdPkMixin, Base):
    name: Mapped[str | None] = mapped_column(String(64))
    surname: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(50), unique=True)

    password: Mapped[str] = mapped_column(String(500))
    reg_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_superuser: Mapped[bool] = mapped_column(default=False)
    photo: Mapped[str | None] = mapped_column(String(500))
    access_token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", create_type=True),
        nullable=False,
        server_default=UserRole.teacher.name,
    )

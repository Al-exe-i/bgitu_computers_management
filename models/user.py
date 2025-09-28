from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from sqlalchemy import String, DateTime
from datetime import datetime
from models.mixins.int_id_pk_mixin import IntIdPkMixin


class User(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(String(64))
    surname: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(50), unique=True)
    telegram_id: Mapped[str | None] = mapped_column(String(16))
    telegram_id_confirmed: Mapped[bool] = mapped_column(default=False)
    password: Mapped[str] = mapped_column(String(500))
    reg_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    photo: Mapped[str | None] = mapped_column(String(500))
from typing import Any
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixins import IntIdPkMixin


class SpecTemplate(IntIdPkMixin, Base):
    """Шаблон характеристик оборудования.

    Позволяет один раз описать набор характеристик (например, типовую
    конфигурацию компьютера) и применять его сразу к нескольким единицам
    оборудования, не заполняя каждую вручную.
    """

    name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Тип оборудования (значение HardwareType, например "computer") храним строкой,
    # чтобы не завязываться на enum-тип в БД
    hardware_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    specs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

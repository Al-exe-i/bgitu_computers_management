from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from modules.inventory.schemas.hardware import (
    HardwareFullResponse,
    HardwareGridItem,
    HardwareShortResponse,
)
from modules.inventory.types import RoomType


class AudienceBase(BaseModel):
    number: int = Field(gt=0, description="Номер аудитории внутри корпуса")
    floor: int
    room_type: RoomType = RoomType.educational
    description: str | None = Field(
        default=None,
        max_length=200,
        description="Название или номер аудитории (напр. '105')",
    )
    office_id: int = Field(description="ID офиса/здания/этажа")
    width: int = Field(gt=0, le=20, description="Ширина сетки")
    height: int = Field(gt=0, le=20, description="Высота сетки")
    landmarks: dict | None = None


class AudienceCreate(AudienceBase):
    hardware: list[HardwareGridItem] = Field(default_factory=list)


class AudienceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=200)
    office_id: int | None = None
    floor: int | None = None
    room_type: RoomType | None = None
    width: int | None = Field(default=None, gt=0, le=20)
    height: int | None = Field(default=None, gt=0, le=20)
    hardware: list[HardwareGridItem] | None = None
    landmarks: dict | None = None

    @field_validator("room_type")
    @classmethod
    def reject_null_room_type(cls, value):
        if value is None:
            raise ValueError("Тип кабинета не может быть пустым")
        return value


class AudienceResponse(AudienceBase):
    id: int
    public_id: UUID
    hardware: list[HardwareFullResponse] = Field(default_factory=list)


class AudienceShortResponse(AudienceBase):
    id: int
    public_id: UUID
    hardware: list[HardwareShortResponse] = Field(default_factory=list)


class AudienceLandmarks(BaseModel):
    north: str | None = Field(default=None, max_length=128)
    south: str | None = Field(default=None, max_length=128)
    west: str | None = Field(default=None, max_length=128)
    east: str | None = Field(default=None, max_length=128)

    model_config = ConfigDict(extra="forbid")

from pydantic import BaseModel, Field, ConfigDict
from schemas.hardware import HardwareFullResponse, HardwareShortResponse, HardwareGridItem


class AudienceBase(BaseModel):
    id: int
    floor: int
    description: str | None = Field(default=None, max_length=200,
                                    description="Название или номер аудитории (напр. '105')")
    office_id: int = Field(description="ID офиса/здания/этажа")
    width: int = Field(gt=0, le=20, description="Ширина сетки")
    height: int = Field(gt=0, le=20, description="Высота сетки")
    landmarks: dict | None = None


class AudienceCreate(AudienceBase):
    hardware: list[HardwareGridItem] = Field(default_factory=list)


class AudienceUpdate(BaseModel):
    description: str | None = None
    office_id: int | None = None
    floor: int | None = None
    width: int | None = None
    height: int | None = None
    hardware: list[HardwareGridItem] | None = None
    landmarks: dict | None = None


class AudienceResponse(AudienceBase):
    hardware: list[HardwareFullResponse] = Field(default_factory=list)


class AudienceShortResponse(AudienceBase):
    hardware: list[HardwareShortResponse] = Field(default_factory=list)

class AudienceLandmarks(BaseModel):
    north: str | None = Field(default=None, max_length=128)
    south: str | None = Field(default=None, max_length=128)
    west: str | None = Field(default=None, max_length=128)
    east: str | None = Field(default=None, max_length=128)

    model_config = ConfigDict(extra="forbid")

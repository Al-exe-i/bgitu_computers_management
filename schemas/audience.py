from pydantic import BaseModel, Field
from schemas.hardware import HardwareCreate, HardwareFullResponse, HardwareShortResponse


class AudienceBase(BaseModel):
    id: int
    floor: int
    description: str | None = Field(default=None, max_length=200, description="Название или номер аудитории (напр. '105')")
    office_id: int = Field(description="ID офиса/здания/этажа")
    width: int = Field(gt=0, le=15, description="Ширина сетки")
    height: int = Field(gt=0, le=15, description="Высота сетки")

class AudienceCreate(AudienceBase):
    hardware: list[HardwareCreate] = []

class AudienceUpdate(BaseModel):
    description: str | None = None
    office_id: int | None = None
    width: int | None = None
    height: int | None = None
    hardware: list[HardwareCreate] | None = None

class AudienceResponse(AudienceBase):
    hardware: list[HardwareFullResponse] = []

class AudienceShortResponse(AudienceBase):
    hardware: list[HardwareShortResponse] = []
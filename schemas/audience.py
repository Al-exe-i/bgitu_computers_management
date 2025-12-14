from typing import List
from pydantic import BaseModel, Field
from schemas.hardware import HardwareCreate, HardwareResponse


class AudienceBase(BaseModel):
    id: int
    description: str | None = Field(max_length=200, description="Название или номер аудитории (напр. '105')")
    office_id: int = Field(description="ID офиса/здания/этажа")
    width: int = Field(gt=0, le=15, description="Ширина сетки")
    height: int = Field(gt=0, le=15, description="Высота сетки")

class AudienceCreate(AudienceBase):
    hardware: List[HardwareCreate] = []

class AudienceUpdate(BaseModel):
    description: str | None = None
    office_id: int | None = None
    width: int | None = None
    height: int | None = None

class AudienceResponse(AudienceBase):
    hardware: List[HardwareResponse] = []
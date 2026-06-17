from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.hardware import HardwareType


class SpecTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    hardware_type: HardwareType
    specs: dict = Field(default_factory=dict)


class SpecTemplateCreate(SpecTemplateBase):
    pass


class SpecTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    specs: dict | None = None


class SpecTemplateResponse(SpecTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

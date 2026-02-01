from pydantic import BaseModel, Field
from models.hardware import HardwareType
from schemas.hardware_file import HardwareFileResponse


class HardwareBase(BaseModel):
    type: HardwareType
    x: int = Field(ge=0, description="Координата X в сетке (колонка)")
    y: int = Field(ge=0, description="Координата Y в сетке (ряд)")
    state: bool = Field(default=True)
    description: str | None = Field(default=None, max_length=255)
    inv_number: str | None = Field(default=None, max_length=32)
    title: str | None = Field(default=None, max_length=64)


class HardwareCreate(HardwareBase):
    id: int | None = None


class HardwareUpdate(BaseModel):
    type: HardwareType | str = None
    x: int | None = Field(None, ge=0)
    y: int | None = Field(None, ge=0)
    state: bool | None = None
    description: str | None = None
    inv_number: str | None = None
    title: str | None = None
    files: list[HardwareFileResponse] | None = None


class HardwareShortResponse(HardwareBase):
    id: int
    audience_id: int


class HardwareFullResponse(HardwareShortResponse):
    files: list[HardwareFileResponse] | None = []

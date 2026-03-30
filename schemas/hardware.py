from pydantic import BaseModel, Field
from models.hardware import HardwareType
from schemas.hardware_file import HardwareFileResponse


class HardwareBase(BaseModel):
    type: HardwareType
    x: int = Field(ge=0, description="Координата X в сетке (левая колонка)")
    y: int = Field(ge=0, description="Координата Y в сетке (верхний ряд)")
    width: int = Field(default=1, ge=1, description="Ширина оборудования в клетках")
    height: int = Field(default=1, ge=1, description="Высота оборудования в клетках")

    state: bool = Field(default=True)
    description: str | None = Field(default=None, max_length=255)
    inv_number: str | None = Field(default=None, max_length=32)
    title: str | None = Field(default=None, max_length=64)


class HardwareCreate(HardwareBase):
    pass


class HardwareGridItem(HardwareBase):
    id: int | None = None


class HardwareUpdate(BaseModel):
    type: HardwareType | None = None
    x: int | None = Field(default=None, ge=0)
    y: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)

    state: bool | None = None
    description: str | None = Field(default=None, max_length=255)
    inv_number: str | None = Field(default=None, max_length=32)
    title: str | None = Field(default=None, max_length=64)
    files: list[HardwareFileResponse] | None = None


class HardwareShortResponse(HardwareBase):
    id: int
    audience_id: int


class HardwareFullResponse(HardwareShortResponse):
    files: list[HardwareFileResponse] = Field(default_factory=list)
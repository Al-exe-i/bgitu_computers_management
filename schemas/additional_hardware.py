from typing import Dict, Any

from pydantic import BaseModel

from models.additional_hardware import HardwareType


class AdditionalHardwareBase(BaseModel):
    type: HardwareType
    name: str
    description: str | None = None
    is_functional: bool = True
    specifications: Dict[str, Any] | None = None

class AdditionalHardwareCreate(AdditionalHardwareBase):
    audience_id: int

class AdditionalHardwareUpdate(BaseModel):
    type: HardwareType | None = None
    name: str | None = None
    description: str | None = None
    is_functional: bool | None = None
    specifications: Dict[str, Any] = None

class AdditionalHardware(AdditionalHardwareBase):
    id: int
    audience_id: int
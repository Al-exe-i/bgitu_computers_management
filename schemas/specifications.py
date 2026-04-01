from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class MemoryUnit(str, Enum):
    mb = "mb"
    gb = "gb"
    tb = "tb"

class ComputerSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu_model: str | None = Field(default=None, max_length=128)
    cpu_frequency_ghz: float | None = Field(default=None, gt=0)
    cpu_cores: int | None = Field(default=None, ge=1)

    ram_amount: int | None = Field(default=None, ge=1)
    ram_unit: MemoryUnit | None = None

    storage_amount: int | None = Field(default=None, ge=1)
    storage_unit: MemoryUnit | None = None

    purchase_year: int | None = Field(default=None, ge=2000, le=2100)

class SwitchSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ports_count: int | None = Field(default=None, ge=1)
    managed: bool | None = None

class EmptySpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from schemas.audience import AudienceShortResponse


class OfficeBase(BaseModel):
    id: int = Field(gt=0)
    address: str = Field(min_length=1, max_length=100)


class OfficeCreate(OfficeBase):
    pass


class OfficeResponse(OfficeBase):
    audiences: List[AudienceShortResponse]


class OfficeShort(OfficeBase):
    audiences_count: int | None = None
    faulty_hw_count: int | None = None


class OfficeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = Field(default=None, min_length=1, max_length=100)

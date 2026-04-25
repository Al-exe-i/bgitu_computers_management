from typing import List
from pydantic import BaseModel
from schemas.audience import AudienceShortResponse


class OfficeBase(BaseModel):
    id: int
    address: str


class OfficeCreate(OfficeBase):
    pass


class OfficeResponse(OfficeBase):
    audiences: List[AudienceShortResponse]


class OfficeShort(OfficeBase):
    audiences_count: int | None = None
    faulty_hw_count: int | None = None


class OfficeUpdate(BaseModel):
    address: str | None = None

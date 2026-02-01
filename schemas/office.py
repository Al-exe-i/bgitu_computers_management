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
    pass


class OfficeUpdate(BaseModel):
    address: str | None = None

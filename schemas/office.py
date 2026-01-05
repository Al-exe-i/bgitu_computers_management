from typing import List
from pydantic import BaseModel
from schemas.audience import AudienceShortResponse


class OfficeBase(BaseModel):
    address: str
    audiences: List[AudienceShortResponse]

class Office(OfficeBase):
    id: int

class OfficeUpdate(BaseModel):
    address: str | None = None
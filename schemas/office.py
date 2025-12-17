from typing import List
from pydantic import BaseModel
from schemas.audience import AudienceResponse


class OfficeBase(BaseModel):
    address: str
    audiences: List[AudienceResponse]

class Office(OfficeBase):
    id: int

class OfficeUpdate(BaseModel):
    address: str | None = None
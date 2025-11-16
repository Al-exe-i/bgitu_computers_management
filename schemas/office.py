from typing import List

from pydantic import BaseModel
from schemas.audience import AudienceRead


class OfficeBase(BaseModel):
    address: str
    audiences: List[AudienceRead]

class Office(OfficeBase):
    id: int

class OfficeUpdate(BaseModel):
    address: str | None = None
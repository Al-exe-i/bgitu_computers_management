from typing import List

from pydantic import BaseModel

from schemas.audience import Audience


class OfficeBase(BaseModel):
    address: str
    audiences: List[Audience]

class Office(OfficeBase):
    id: int

class OfficeUpdate(BaseModel):
    address: str | None = None
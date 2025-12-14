from typing import List

from pydantic import BaseModel


class OfficeBase(BaseModel):
    address: str
    #audiences: List[AudienceRead]

class Office(OfficeBase):
    id: int

class OfficeUpdate(BaseModel):
    address: str | None = None
from typing import List

from pydantic import BaseModel

from schemas.audience import Audience
from schemas.computer import Computer


class Row(BaseModel):
    id: int
    name: str
    audience: Audience
    computers: List[Computer]
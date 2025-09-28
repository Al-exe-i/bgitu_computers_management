from pydantic import BaseModel, Field
from models.audience import AudienceType


class AudienceBase(BaseModel):
    id: int

class Audience(AudienceBase):
    rows: dict[str, list[dict]] | None = None
    additional_hardware: str | None = None
    type: AudienceType = Field(default=AudienceType.row)
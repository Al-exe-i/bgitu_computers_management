from pydantic import BaseModel, Field
from models.auditorium import AuditoriumTypes


class AuditoriumBase(BaseModel):
    id: int

class Auditorium(AuditoriumBase):
    rows: dict[str, list[dict]] | None = None
    additional_hardware: str | None = None
    type: AuditoriumTypes = Field(default=AuditoriumTypes.row)
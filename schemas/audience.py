from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from models.audience import AudienceType
from schemas.row import Row, RowCreateRequest


class AudienceBase(BaseModel):
    type: AudienceType = AudienceType.row
    additional_hardware: Dict[str, Any] | None = None


class AudienceCreate(AudienceBase):
    pass


class AudienceUpdate(BaseModel):
    type: AudienceType | None = None
    additional_hardware: Dict[str, Any] | None = None


class Audience(AudienceBase):
    id: int
    rows: List[Row] = []


class AudienceCreateRequest(BaseModel):
    id: int
    type: AudienceType = AudienceType.row
    rows: List['RowCreateRequest'] = Field(min_length=1)

    @field_validator('rows')
    @classmethod
    def validate_row_names_unique(cls, v):
        names = [row.name for row in v]
        if len(names) != len(set(names)):
            raise ValueError('Row names must be unique')
        return v
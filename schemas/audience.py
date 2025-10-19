from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from models.audience import AudienceType
from schemas.additional_hardware import AdditionalHardware
from schemas.row import Row, RowCreateRequest


class AudienceBase(BaseModel):
    type: AudienceType = AudienceType.row


class AudienceCreate(AudienceBase):
    pass


class AudienceUpdate(BaseModel):
    type: AudienceType | None = None


class Audience(AudienceBase):
    id: int
    rows: List[Row] = []
    additional_hardware: List[AdditionalHardware] = []


class AudienceCreateRequest(BaseModel):
    id: int
    type: AudienceType = AudienceType.row
    rows: List['RowCreateRequest'] = Field(min_length=1)
    office_id: int

    @field_validator('rows')
    @classmethod
    def validate_row_names_unique(cls, v):
        names = [row.name for row in v]
        if len(names) != len(set(names)):
            raise ValueError('Row names must be unique')
        return v
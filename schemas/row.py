from typing import List

from pydantic import BaseModel, Field, field_validator

from schemas.computer import Computer


class RowBase(BaseModel):
    name: str


class RowCreate(RowBase):
    audience_id: int


class RowUpdate(BaseModel):
    name: str | None = None
    audience_id: int | None = None


class Row(RowBase):
    id: int
    audience_id: int
    computers: List[Computer] = []


class RowCreateRequest(BaseModel):
    name: str = Field(..., pattern=r'^row_\d{1,2}$', max_length=6)
    computers_count: int = Field(..., ge=1, le=10)
    broken_ids: List[int] = []

    @field_validator('name')
    @classmethod
    def validate_row_number(cls, v):
        # Проверяем что номер ряда не больше 10
        if v.startswith('row_'):
            try:
                num = int(v[4:])
                if num > 10:
                    raise ValueError("Row number can't exceed 10")
            except ValueError:
                pass
        return v
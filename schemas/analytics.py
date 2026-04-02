from typing import Any
from pydantic import BaseModel, Field
from models.hardware import HardwareType


class NumberRange(BaseModel):
    gte: int | float | None = None
    lte: int | float | None = None


class HardwareAnalyticsFilters(BaseModel):
    office_ids: list[int] | None = None
    floors: list[int] | None = None
    audience_ids: list[int] | None = None
    states: list[bool] | None = None
    types: list[HardwareType] | None = None

    cpu_frequency_ghz: NumberRange | None = None
    cpu_cores: NumberRange | None = None
    ram_amount: NumberRange | None = None
    storage_amount: NumberRange | None = None
    purchase_year: NumberRange | None = None

    ports_count: NumberRange | None = None
    managed: bool | None = None

    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class HardwareAnalyticsItem(BaseModel):
    id: int
    type: HardwareType
    state: bool
    title: str | None = None
    inv_number: str | None = None
    description: str | None = None

    office_id: int
    office_address: str
    floor: int
    audience_id: int

    x: int
    y: int
    width: int
    height: int

    specs: dict[str, Any]


class HardwareAnalyticsSummary(BaseModel):
    total: int
    working: int
    broken: int
    by_type: dict[str, int]


class HardwareAnalyticsResponse(BaseModel):
    items: list[HardwareAnalyticsItem]
    total: int
    summary: HardwareAnalyticsSummary


class FilterOption(BaseModel):
    value: int | str | bool
    label: str


class HardwareAnalyticsFilterOptions(BaseModel):
    offices: list[FilterOption]
    floors: list[FilterOption]
    audiences: list[FilterOption]
    states: list[FilterOption]
    types: list[FilterOption]
    spec_filters: list[dict[str, Any]]
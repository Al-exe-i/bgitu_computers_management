from fastapi import APIRouter

from dependencies.auth import admin_dep
from dependencies.inventory import inventory_analytics_queries_dep
from modules.inventory.schemas.analytics import (
    HardwareAnalyticsFilterOptions,
    HardwareAnalyticsFilters,
    HardwareAnalyticsResponse,
)

router = APIRouter()


@router.post("", response_model=HardwareAnalyticsResponse)
async def get_hardware_analytics(
    filters: HardwareAnalyticsFilters,
    queries: inventory_analytics_queries_dep,
    _user: admin_dep,
):
    return await queries.get_hardware(filters)


@router.get("/filter-options", response_model=HardwareAnalyticsFilterOptions)
async def get_hardware_filter_options(
    queries: inventory_analytics_queries_dep,
    _user: admin_dep,
):
    return await queries.get_filter_options()

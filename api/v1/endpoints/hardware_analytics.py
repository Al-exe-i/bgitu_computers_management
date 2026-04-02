from fastapi import APIRouter

from dependencies.analytics import analytics_service_dep
from dependencies.auth import admin_dep
from schemas.analytics import (
    HardwareAnalyticsFilters,
    HardwareAnalyticsResponse,
    HardwareAnalyticsFilterOptions,
)

router = APIRouter()


@router.post("", response_model=HardwareAnalyticsResponse)
async def get_hardware_analytics(
        filters: HardwareAnalyticsFilters,
        service: analytics_service_dep,
        user: admin_dep
):
    return await service.get_hardware(filters)


@router.get("/filter-options", response_model=HardwareAnalyticsFilterOptions)
async def get_hardware_filter_options(
        service: analytics_service_dep,
        user: admin_dep
):
    return await service.get_filter_options()

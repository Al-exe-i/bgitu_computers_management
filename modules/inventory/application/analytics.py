from modules.inventory.ports import HardwareAnalyticsServicePort
from modules.inventory.schemas.analytics import (
    HardwareAnalyticsFilterOptions,
    HardwareAnalyticsFilters,
    HardwareAnalyticsResponse,
)


class InventoryAnalyticsQueries:
    def __init__(self, service: HardwareAnalyticsServicePort) -> None:
        self.service = service

    async def get_hardware(
        self,
        filters: HardwareAnalyticsFilters,
    ) -> HardwareAnalyticsResponse:
        return await self.service.get_hardware(filters)

    async def get_filter_options(self) -> HardwareAnalyticsFilterOptions:
        return await self.service.get_filter_options()

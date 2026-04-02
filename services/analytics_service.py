from repositories.analytics_repo import HardwareAnalyticsRepository
from schemas.analytics import (
    HardwareAnalyticsFilters,
    HardwareAnalyticsItem,
    HardwareAnalyticsResponse,
    HardwareAnalyticsSummary,
    HardwareAnalyticsFilterOptions,
)


class HardwareAnalyticsService:
    def __init__(self, repo: HardwareAnalyticsRepository):
        self.repo = repo

    async def get_hardware(self, filters: HardwareAnalyticsFilters) -> HardwareAnalyticsResponse:
        rows = await self.repo.list(filters)
        total = await self.repo.count_total(filters)
        summary = await self.repo.summary(filters)

        items = []
        for hw, audience_id, floor, office_id, office_address in rows:
            items.append(
                HardwareAnalyticsItem(
                    id=hw.id,
                    type=hw.type,
                    state=hw.state,
                    title=hw.title,
                    inv_number=hw.inv_number,
                    description=hw.description,
                    office_id=office_id,
                    office_address=office_address,
                    floor=floor,
                    audience_id=audience_id,
                    x=hw.x,
                    y=hw.y,
                    width=hw.width,
                    height=hw.height,
                    specs=hw.specs,
                )
            )

        return HardwareAnalyticsResponse(
            items=items,
            total=total,
            summary=HardwareAnalyticsSummary(**summary),
        )

    async def get_filter_options(self) -> HardwareAnalyticsFilterOptions:
        data = await self.repo.filter_options()

        spec_filters = [
            {"key": "cpu_frequency_ghz", "label": "Частота CPU", "kind": "range", "unit": "ГГц", "types": ["computer", "server"]},
            {"key": "cpu_cores", "label": "Ядра CPU", "kind": "range", "types": ["computer", "server"]},
            {"key": "ram_amount", "label": "ОЗУ", "kind": "range", "types": ["computer", "server"]},
            {"key": "storage_amount", "label": "ПЗУ", "kind": "range", "types": ["computer", "server"]},
            {"key": "purchase_year", "label": "Год закупки", "kind": "range", "types": ["computer", "server"]},
            {"key": "ports_count", "label": "Кол-во портов", "kind": "range", "types": ["switch"]},
            {"key": "managed", "label": "Управляемый", "kind": "boolean", "types": ["switch"]},
        ]

        return HardwareAnalyticsFilterOptions(
            **data,
            spec_filters=spec_filters,
        )
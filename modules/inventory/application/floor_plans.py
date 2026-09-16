from typing import Protocol

from modules.administration.public import AuditLogger
from modules.inventory.schemas.floor_plan import (
    FloorInfo,
    FloorPlanResponse,
    FloorPlanUpdate,
)


class FloorPlanServicePort(Protocol):
    async def get_info(self, office_id: int, floor: int) -> FloorInfo: ...
    async def update_info(
        self, office_id: int, floor: int, data: FloorInfo
    ) -> FloorInfo: ...
    async def get(self, office_id: int, floor: int) -> FloorPlanResponse: ...
    async def update(
        self, office_id: int, floor: int, data: FloorPlanUpdate
    ) -> FloorPlanResponse: ...


class InventoryFloorPlanUseCases:
    def __init__(self, service: FloorPlanServicePort):
        self.service = service

    async def get_info(self, office_id: int, floor: int) -> FloorInfo:
        return await self.service.get_info(office_id, floor)

    async def update_info(
        self, office_id: int, floor: int, data: FloorInfo, audit: AuditLogger
    ) -> FloorInfo:
        result = await self.service.update_info(office_id, floor, data)
        await audit.log(
            action="floor.info_update",
            entity_type="office",
            entity_id=office_id,
            payload={"floor": floor, "changed_fields": sorted(data.model_fields_set)},
        )
        return result

    async def get(self, office_id: int, floor: int) -> FloorPlanResponse:
        return await self.service.get(office_id, floor)

    async def update(
        self, office_id: int, floor: int, data: FloorPlanUpdate, audit: AuditLogger
    ) -> FloorPlanResponse:
        result = await self.service.update(office_id, floor, data)
        await audit.log(
            action="floor_plan.update",
            entity_type="office",
            entity_id=office_id,
            payload={
                "floor": floor,
                "width": data.width,
                "height": data.height,
                "rooms_count": len(data.rooms),
                "revision": result.revision,
            },
        )
        return result

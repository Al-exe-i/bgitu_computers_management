from core.exceptions.floor_plan import FloorPlanConflictError, FloorPlanRoomError
from modules.inventory.repositories.floor_plans import FloorPlanRepository
from modules.inventory.schemas.floor_plan import (
    FloorInfo,
    FloorPlanResponse,
    FloorPlanUpdate,
    FloorRoom,
    RoomPlacement,
)


class FloorPlanService:
    def __init__(self, repo: FloorPlanRepository):
        self.repo = repo

    async def get_info(self, office_id: int, floor: int) -> FloorInfo:
        plan = await self.repo.get(office_id, floor)
        return FloorInfo.model_validate(plan) if plan is not None else FloorInfo()

    async def update_info(
        self, office_id: int, floor: int, data: FloorInfo
    ) -> FloorInfo:
        plan = await self.repo.get(office_id, floor, for_update=True)
        await self.repo.update_info(plan, data.model_dump(exclude_unset=True))
        return FloorInfo.model_validate(plan)

    async def get(self, office_id: int, floor: int) -> FloorPlanResponse:
        plan = await self.repo.get(office_id, floor)
        rooms = await self.repo.list_rooms(office_id, floor)
        return self._response(office_id, floor, plan, rooms)

    async def update(
        self, office_id: int, floor: int, data: FloorPlanUpdate
    ) -> FloorPlanResponse:
        plan = await self.repo.get(office_id, floor, for_update=True)
        if plan.revision != data.revision:
            raise FloorPlanConflictError()
        rooms = await self.repo.list_rooms(office_id, floor)
        allowed = {room.public_id for room in rooms}
        if any(room.audience_public_id not in allowed for room in data.rooms):
            raise FloorPlanRoomError()
        positions = {
            str(room.audience_public_id): room.model_dump(
                mode="json", exclude={"audience_public_id"}
            )
            for room in data.rooms
        }
        landmarks = (
            data.landmarks.model_dump()
            if "landmarks" in data.model_fields_set
            else plan.landmarks
        )
        await self.repo.save(plan, data.width, data.height, positions, landmarks)
        return self._response(office_id, floor, plan, rooms)

    @staticmethod
    def _response(office_id, floor, plan, rooms) -> FloorPlanResponse:
        positions = plan.positions if plan is not None else {}
        return FloorPlanResponse(
            office_id=office_id,
            floor=floor,
            width=plan.width if plan is not None else 20,
            height=plan.height if plan is not None else 12,
            revision=plan.revision if plan is not None else 0,
            landmarks=(plan.landmarks or {}) if plan is not None else {},
            rooms=[
                FloorRoom(
                    audience_public_id=room.public_id,
                    number=room.number,
                    room_type=room.room_type,
                    description=room.description,
                    placement=RoomPlacement(
                        audience_public_id=room.public_id,
                        **positions[str(room.public_id)],
                    )
                    if str(room.public_id) in positions
                    else None,
                )
                for room in rooms
            ],
        )

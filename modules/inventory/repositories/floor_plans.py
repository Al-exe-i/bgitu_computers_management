from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import OfficeNotFoundError
from modules.inventory.models.audience import Audience
from modules.inventory.models.floor_plan import FloorPlan
from modules.inventory.models.office import Office


class FloorPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self, office_id: int, floor: int, *, for_update: bool = False
    ) -> FloorPlan | None:
        office = await self.session.scalar(
            select(Office.id)
            .where(Office.id == office_id)
            .with_for_update(read=True, key_share=True)
        )
        if office is None:
            raise OfficeNotFoundError()
        if for_update:
            await self.session.execute(
                insert(FloorPlan)
                .values(office_id=office_id, floor=floor)
                .on_conflict_do_nothing()
            )
        query = select(FloorPlan).where(
            FloorPlan.office_id == office_id, FloorPlan.floor == floor
        )
        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def list_rooms(self, office_id: int, floor: int):
        query = (
            select(Audience)
            .where(Audience.office_id == office_id, Audience.floor == floor)
            .order_by(Audience.number, Audience.id)
        )
        return (await self.session.scalars(query)).all()

    async def update_info(self, plan: FloorPlan, changes: dict) -> None:
        for key, value in changes.items():
            setattr(plan, key, value)
        await self.session.flush()

    async def save(
        self, plan: FloorPlan, width: int, height: int, positions: dict, landmarks: dict
    ) -> None:
        plan.width = width
        plan.height = height
        plan.positions = positions
        plan.landmarks = landmarks
        plan.revision += 1
        await self.session.flush()

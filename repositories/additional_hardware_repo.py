from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.additional_hardware import AdditionalHardwareCreate, AdditionalHardwareUpdate
from models.additional_hardware import AdditionalHardware


class AdditionalHardwareRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, hardware_data: AdditionalHardwareCreate) -> AdditionalHardware:
        hardware = AdditionalHardware(**hardware_data.model_dump())
        self.db.add(hardware)
        await self.db.commit()
        await self.db.refresh(hardware)
        return hardware

    async def get_by_audience(self, audience_id: int) -> Sequence[AdditionalHardware]:
        result = await self.db.execute(
            select(AdditionalHardware).where(
                AdditionalHardware.audience_id == audience_id
            )
        )
        return result.scalars().all()

    async def get(self, hardware_id: int) -> AdditionalHardware | None:
        result = await self.db.execute(
            select(AdditionalHardware).where(
                AdditionalHardware.id == hardware_id
            )
        )
        return result.scalars().first()


    async def update(self, hardware: AdditionalHardware, data: AdditionalHardwareUpdate) -> AdditionalHardware:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(hardware, field, value)

        await self.db.commit()
        await self.db.refresh(hardware)
        return hardware

    async def delete(self, hardware: AdditionalHardware) -> None:
        await self.db.delete(hardware)
        await self.db.commit()

    async def delete_all_for_audience(self, audience_id: int) -> int:
        result = await self.db.execute(
            select(AdditionalHardware).where(
                AdditionalHardware.audience_id == audience_id
            )
        )
        hardware_list = result.scalars().all()

        for h in hardware_list:
            await self.db.delete(h)

        await self.db.commit()
        return len(hardware_list)

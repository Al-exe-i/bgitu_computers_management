from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import Hardware


class HardwareRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, hardware_id: int) -> Hardware | None:
        stmt = select(Hardware).where(Hardware.id == hardware_id).options(selectinload(Hardware.files))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_audience_id(self, audience_id: int) -> Sequence[Hardware]:
        stmt = select(Hardware).where(Hardware.audience_id == audience_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, hardware: Hardware) -> Hardware:
        self.session.add(hardware)
        await self.session.flush()
        await self.session.refresh(hardware)
        return hardware

    async def update(self, hardware_id: int, data: dict) -> Hardware | None:
        hw = await self.get_by_id(hardware_id)
        if not hw:
            return None
        for k, v in data.items():
            setattr(hw, k, v)
        await self.session.flush()
        await self.session.refresh(hw)
        return hw

    async def delete(self, hardware_id: int) -> None:
        hw = await self.get_by_id(hardware_id)
        if hw:
            await self.session.delete(hw)
            await self.session.flush()

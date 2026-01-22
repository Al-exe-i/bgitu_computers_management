from typing import Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import Hardware


class HardwareRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def retrieve_session(self) -> AsyncSession:
        return self.session

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
        await self.session.commit()
        await self.session.refresh(hardware)
        return hardware

    async def update(self, hardware_id: int, data: dict) -> Hardware | None:
        stmt = (
            update(Hardware)
            .where(Hardware.id == hardware_id)
            .values(**data)
            .returning(Hardware)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()

    async def delete(self, hardware_id: int):
        stmt = delete(Hardware).where(Hardware.id == hardware_id)
        await self.session.execute(stmt)
        await self.session.commit()
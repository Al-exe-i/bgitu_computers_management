from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.audience import Audience


async def get_all(db: AsyncSession) -> Sequence[Audience]:
    result = await db.execute(select(Audience))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, aud_id: int) -> Audience | None:
    result = await db.execute(select(Audience).where(Audience.id == aud_id))
    return result.scalars().first()

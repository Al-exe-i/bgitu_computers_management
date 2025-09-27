from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.auditorium import Auditorium


async def get_all(db: AsyncSession) -> Sequence[Auditorium]:
    result = await db.execute(select(Auditorium))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, aud_id: int) -> Auditorium | None:
    result = await db.execute(select(Auditorium).where(Auditorium.id == aud_id))
    return result.scalars().first()

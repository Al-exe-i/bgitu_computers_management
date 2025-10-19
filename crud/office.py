from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models import Audience, Row
from models.office import Office


async def get_office(db: AsyncSession, office_id: int) -> Office | None:
    stmt = (
        select(Office)
        .where(Office.id == office_id)
        .options(
            selectinload(Office.audiences)
            .selectinload(Audience.rows)
            .selectinload(Row.computers),
            selectinload(Office.audiences).selectinload(Audience.additional_hardware)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()



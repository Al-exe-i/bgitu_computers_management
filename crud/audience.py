from typing import Sequence, Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models import Audience
from models.audience import Audience, Row, Computer
from schemas.audience import AudienceCreateRequest


async def get_all(db: AsyncSession) -> Sequence[Audience]:
    result = await db.execute(select(Audience)
                              .options(selectinload(Audience.rows).selectinload(Row.computers)))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, aud_id: int) -> Audience | None:
    result = await db.execute(
        select(Audience)
        .where(Audience.id == aud_id)
        .options(
            selectinload(Audience.rows).selectinload(Row.computers)
        )
    )
    return result.scalars().first()


async def create_audience(db: AsyncSession, audience_data: AudienceCreateRequest) -> Audience | None:
    try:
        db_audience = Audience(
            id=audience_data.id,
            type=audience_data.type,
            additional_hardware=None
        )
        db.add(db_audience)
        await db.flush()

        # Создаем ряды и компьютеры
        for row_data in audience_data.rows:
            db_row = Row(
                name=row_data.name,
                audience_id=db_audience.id
            )
            db.add(db_row)
            await db.flush()

            # Создаем компьютеры для ряда
            for i in range(1, row_data.computers_count + 1):
                computer = Computer(
                    name=f"PC{row_data.name.replace('row_', '')}_{i:02d}",
                    row_id=db_row.id,
                    state=True
                )
                db.add(computer)

        await db.commit()
        await db.refresh(db_audience)
        return db_audience

    except Exception as e:
        await db.rollback()


async def delete_audience(db: AsyncSession, audience_id: int) -> bool:
    db_audience = await get_by_id(db, audience_id)
    if not db_audience:
        return False

    await db.delete(db_audience)
    await db.commit()
    return True



from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.audience import Audience, Row, Computer
from schemas.audience import AudienceCreateRequest, AudienceUpdate


async def get_all(db: AsyncSession) -> Sequence[Audience]:
    stmt = (
        select(Audience).
        options
            (
            selectinload(Audience.rows).selectinload(Row.computers),
            selectinload(Audience.additional_hardware)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_id(db: AsyncSession, aud_id: int) -> Audience | None:
    stmt = (
        select(Audience)
        .where(Audience.id == aud_id)
        .options(
            selectinload(Audience.rows).selectinload(Row.computers),
            selectinload(Audience.additional_hardware)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_audience(db: AsyncSession, audience_data: AudienceCreateRequest) -> Audience | None:
    db_audience = Audience(
        id=audience_data.id,
        type=audience_data.type,
        office_id=audience_data.office_id,
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
                state=False if i in row_data.broken_ids else True,
            )
            db.add(computer)

    await db.commit()
    await db.refresh(db_audience)
    return db_audience


async def update_audience(db: AsyncSession, audience_id: int, update_schema: AudienceUpdate) -> Audience | None:
    audience = await get_by_id(db, audience_id)

    if audience is None:
        raise HTTPException(status_code=404, detail="Audience not found")

    update_data = update_schema.model_dump(exclude_unset=True)
    for(key, value) in update_data.items():
        setattr(audience, key, value)

    await db.commit()
    await db.refresh(audience)

    return audience


async def delete_audience(db: AsyncSession, audience_id: int) -> bool:
    db_audience = await get_by_id(db, audience_id)
    if not db_audience:
        return False

    await db.delete(db_audience)
    await db.commit()
    return True



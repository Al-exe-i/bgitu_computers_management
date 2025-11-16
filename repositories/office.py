from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Audience, Row, Computer
from models.office import Office
from schemas.office import OfficeUpdate


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


async def update_office(db: AsyncSession, schema: OfficeUpdate, orm_model: Office) -> Office:
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(orm_model, field, value)
    await db.commit()
    await db.refresh(orm_model)
    return orm_model


async def count_faulty_computers(db: AsyncSession, office_id: int) -> int:
    stmt = (
        select(func.count(Computer.id))
        .join(Row)
        .join(Audience)
        .join(Office)
        .where(
            Office.id == office_id,
            Computer.state == False
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


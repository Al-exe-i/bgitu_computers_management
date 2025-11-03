from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Computer
from schemas.computer import ComputerUpdate


async def update_computer(db: AsyncSession, computer_id: int, update_schema: ComputerUpdate) -> Computer | None:
    stmt = select(Computer).where(Computer.id == computer_id)
    result = await db.execute(stmt)
    computer = result.scalar_one_or_none()

    if not computer:
        raise HTTPException(status_code=404, detail="Computer not found")

    update_data = update_schema.model_dump(exclude_unset=True)
    for(key, value) in update_data.items():
        setattr(computer, key, value)

    await db.commit()
    await db.refresh(computer)

    return computer
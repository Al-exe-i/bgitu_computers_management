from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import Computer
from schemas.computer import ComputerUpdate

class ComputerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, computer_id: int) -> Computer | None:
        stmt = select(Computer).where(Computer.id == computer_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, computer: Computer, data: ComputerUpdate) -> Computer | None:
        update_data = data.model_dump(exclude_unset=True)
        for(key, value) in update_data.items():
            setattr(computer, key, value)

        await self.db.commit()
        await self.db.refresh(computer)

        return computer
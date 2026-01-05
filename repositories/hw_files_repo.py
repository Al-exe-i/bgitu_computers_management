from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.hardware_file import HardwareFile


class HardwareFilesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, file_id: int) -> HardwareFile | None:
        stmt = select(HardwareFile).where(HardwareFile.id == file_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, hardware_file: HardwareFile) -> HardwareFile:
        self.db.add(hardware_file)
        await self.db.commit()
        await self.db.refresh(hardware_file)
        return hardware_file

    async def delete(self, file_id: int) -> bool:
        db_file = await self.get_by_id(file_id)
        if db_file:
            await self.db.delete(db_file)
            await self.db.commit()
            return True
        return False
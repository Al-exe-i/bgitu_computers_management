from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.models.office import Office


class OfficeBootstrapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock(self) -> None:
        await self.db.execute(text("LOCK TABLE offices IN SHARE ROW EXCLUSIVE MODE"))

    async def get(self, office_id: int) -> Office | None:
        return await self.db.get(Office, office_id)

    async def get_by_address(self, address: str) -> Office | None:
        return await self.db.scalar(
            select(Office).where(func.lower(Office.address) == address.lower())
        )

    async def create(self, office_id: int, address: str) -> None:
        self.db.add(Office(id=office_id, address=address))
        await self.db.flush()

    async def synchronize_sequence(self) -> None:
        # Explicit seed IDs must not collide with the next automatically assigned ID.
        # Sequence advancement is not transactional; rollback may leave harmless gaps.
        await self.db.execute(
            text("""
            SELECT setval(pg_get_serial_sequence('offices', 'id'),
                GREATEST(COALESCE((SELECT MAX(id) FROM offices), 1),
                    COALESCE(pg_sequence_last_value(pg_get_serial_sequence('offices', 'id')::regclass), 1)),
                true)
        """)
        )

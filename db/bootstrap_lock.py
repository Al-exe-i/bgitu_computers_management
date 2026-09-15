from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresBootstrapLock:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def acquire(self) -> None:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": 4_244_748_214_403_238_731},
        )

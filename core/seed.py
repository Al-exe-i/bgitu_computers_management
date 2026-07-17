import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from core.config import settings

OFFICES = [
    {"id": 1, "address": os.getenv("SEED_OFFICE_1", "Корпус №1")},
    {"id": 2, "address": os.getenv("SEED_OFFICE_2", "Корпус №2")},
]

async def main():
    db_url = str(settings.db.url)
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO offices (id, address)
                VALUES (:id, :address)
                ON CONFLICT (id) DO NOTHING
            """),
            OFFICES,
        )

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

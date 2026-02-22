import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from core.config import settings
from core.security import get_password_hash

OFFICES = [
    {"id": 1, "address": os.getenv("SEED_OFFICE_1", "Office #1")},
    {"id": 2, "address": os.getenv("SEED_OFFICE_2", "Office #2")},
]

USER = {
    "email": "admin@example.com",
    "password": get_password_hash("admin"),
    "is_superuser": True,
    "role": "admin",
    "telegram_id_confirmed": False,
}

async def main():
    db_url = str(settings.db.url)
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO offices (id, address)
                VALUES (:id, :address)
                ON CONFLICT (id) DO UPDATE SET address = EXCLUDED.address
            """),
            OFFICES,
        )

        await conn.execute(
            text("""
                INSERT INTO users (email, password, is_superuser, role, telegram_id_confirmed)
                VALUES (:email, :password, :is_superuser, :role, :telegram_id_confirmed)
                ON CONFLICT (email) DO NOTHING
            """),
            USER,
        )

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
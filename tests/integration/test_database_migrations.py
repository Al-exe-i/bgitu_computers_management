import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from db.base import Base

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="Задайте TEST_POSTGRES_URL для интеграционной проверки PostgreSQL",
)


def migrate(connection, revision):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["connection"] = connection
    command.upgrade(config, revision)
    return config


@pytest.mark.parametrize("populated", [False, True], ids=["fresh", "existing-data"])
def test_migrations_reach_head_without_losing_existing_data(populated):
    async def scenario():
        engine = create_async_engine(
            os.environ["TEST_POSTGRES_URL"], poolclass=NullPool
        )
        # A unique search_path keeps application tables and enum types untouched.
        schema = f"test_bgitu_{uuid4().hex}"
        try:
            async with engine.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            async with engine.connect() as connection:
                await connection.execute(text(f'SET search_path TO "{schema}"'))
                await connection.commit()
                if populated:
                    await connection.run_sync(migrate, "c7e42a9d1b0f")
                    await connection.execute(
                        text(
                            "INSERT INTO offices (id, address) VALUES (1, 'Test building')"
                        )
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO audiences (id, office_id, floor, width, height) "
                            "VALUES (228, 1, 2, 6, 4)"
                        )
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO users (id, email, password, is_superuser, telegram_id_confirmed, photo) "
                            "VALUES (7, 'TEACHER@EXAMPLE.RU', 'test-hash', false, false, 'old.png')"
                        )
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO hardwares (id, audience_id, type, state, x, y) "
                            "VALUES (9, 228, 'computer', true, 1, 1)"
                        )
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO hardware_files (id, hardware_id, file_type, file_path) "
                            "VALUES (5, 9, 'image/png', 'uploads/old.png')"
                        )
                    )
                    await connection.commit()

                config = await connection.run_sync(migrate, "head")
                tables = await connection.run_sync(
                    lambda sync: set(inspect(sync).get_table_names(schema=schema))
                )
                assert tables == set(Base.metadata.tables) | {"alembic_version"}
                heads = await connection.run_sync(
                    lambda sync: MigrationContext.configure(sync).get_current_heads()
                )
                assert set(heads) == set(
                    ScriptDirectory.from_config(config).get_heads()
                )

                if populated:
                    room = (
                        await connection.execute(
                            text(
                                "SELECT number, public_id, room_type, width, height, floor "
                                "FROM audiences WHERE id = 228"
                            )
                        )
                    ).one()
                    assert room.number == 228
                    assert room.public_id is not None
                    assert (room.room_type, room.width, room.height, room.floor) == (
                        "educational",
                        6,
                        4,
                        2,
                    )
                    assert (
                        await connection.scalar(
                            text("SELECT photo FROM users WHERE id = 7")
                        )
                        == "old.png"
                    )
                    assert (
                        await connection.scalar(
                            text("SELECT file_path FROM hardware_files WHERE id = 5")
                        )
                        == "uploads/old.png"
                    )
                    assert (
                        await connection.scalar(
                            text(
                                "SELECT count(*) FROM hardwares WHERE audience_id = 228"
                            )
                        )
                        == 1
                    )
                    assert (
                        await connection.scalar(
                            text(
                                "SELECT count(*) FROM users WHERE lower(email) = 'teacher@example.ru'"
                            )
                        )
                        == 1
                    )
        finally:
            try:
                async with engine.begin() as connection:
                    await connection.execute(
                        text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                    )
            finally:
                await engine.dispose()

    asyncio.run(scenario())

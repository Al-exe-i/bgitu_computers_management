import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from db.base import Base
from db.transaction import SessionTransaction
from modules.identity.adapters.avatar_storage import AvatarStorage
from modules.identity.models.user import User
from modules.identity.repositories.users import UserRepository
from modules.identity.services.users import UserService
from modules.inventory.adapters.hardware_storage import HardwareFileStorage
from modules.inventory.models.audience import Audience
from modules.inventory.models.hardware import Hardware
from modules.inventory.models.hardware_file import HardwareFile
from modules.inventory.models.office import Office
from modules.inventory.repositories.hardware_files import HardwareFilesRepository
from modules.inventory.services.hardware_files import HardwareFileService
from modules.inventory.types import HardwareType
from services.object_storage import LocalObjectStorage
from tests.integration.postgres_proxy import LostCommitReplyProxy
from tests.transaction_helpers import transaction_callbacks

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="Задайте TEST_POSTGRES_URL для проверки файлов при потере ответа COMMIT",
)


def upload(content):
    return SimpleNamespace(
        filename="photo.png",
        content_type="image/png",
        size=len(content),
        read=AsyncMock(side_effect=[content, b""]),
        close=AsyncMock(),
    )


@pytest.mark.parametrize("operation", ["avatar", "attachment"])
@pytest.mark.parametrize("failure", ["flush", "lost-commit-reply"])
def test_files_follow_confirmed_commit_outcome(tmp_path, operation, failure):
    async def scenario():
        url = make_url(os.environ["TEST_POSTGRES_URL"])
        schema = f"test_bgitu_{uuid4().hex}"
        admin = create_async_engine(
            url, poolclass=NullPool, connect_args={"ssl": False}
        )
        connect_args = {"ssl": False, "server_settings": {"search_path": schema}}
        direct = create_async_engine(url, poolclass=NullPool, connect_args=connect_args)
        objects = LocalObjectStorage(tmp_path)
        avatars = AvatarStorage(objects)
        old_photo = await avatars.save(upload(b"old-avatar"))
        old_key = f"avatars/{old_photo}"
        email = "commit-test@example.ru"

        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            async with direct.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            async with async_sessionmaker(direct)() as session:
                session.add(
                    User(id=7, email=email, password="test-hash", photo=old_photo)
                )
                if operation == "attachment":
                    session.add(Office(id=1, address="Test building"))
                    session.add(
                        Audience(
                            id=228, number=228, office_id=1, floor=2, width=6, height=4
                        )
                    )
                    session.add(
                        Hardware(
                            id=9, audience_id=228, type=HardwareType.computer, x=1, y=1
                        )
                    )
                await session.commit()

            async with LostCommitReplyProxy(
                url.host or "127.0.0.1", url.port or 5432
            ) as proxy:
                proxied = create_async_engine(
                    url.set(host="127.0.0.1", port=proxy.listen_port),
                    poolclass=NullPool,
                    connect_args=connect_args,
                )
                try:
                    async with async_sessionmaker(
                        proxied, expire_on_commit=False
                    )() as session:
                        callbacks = transaction_callbacks(session)
                        if operation == "avatar":
                            result = await UserService(
                                UserRepository(session), avatars, **callbacks
                            ).upload_photo(7, upload(b"new-file"))
                            new_key = f"avatars/{result.user.photo}"
                            expected_reference = result.user.photo
                            query = select(User.photo).where(User.id == 7)
                            old_reference = old_photo
                        else:
                            result = await HardwareFileService(
                                files_repo=HardwareFilesRepository(session),
                                hardware=SimpleNamespace(
                                    get=AsyncMock(
                                        return_value=SimpleNamespace(
                                            id=9, audience_id=228
                                        )
                                    )
                                ),
                                storage=HardwareFileStorage(objects),
                                **callbacks,
                            ).update_files(9, [upload(b"new-file")])
                            new_key = result.files[0].file_path
                            expected_reference = new_key
                            query = select(HardwareFile.file_path).where(
                                HardwareFile.hardware_id == 9
                            )
                            old_reference = None

                        if failure == "flush":
                            session.add(User(email=email, password="duplicate-email"))
                        error_type = (
                            IntegrityError if failure == "flush" else DBAPIError
                        )
                        with pytest.raises(error_type) as caught:
                            await asyncio.wait_for(
                                SessionTransaction(session).commit(), timeout=10
                            )
                        if failure == "lost-commit-reply":
                            assert proxy.commit_completed.is_set()
                            assert caught.value.connection_invalidated
                        else:
                            assert not proxy.commit_completed.is_set()
                        await SessionTransaction(session).rollback()
                        assert session.info == {}
                finally:
                    await proxied.dispose()

            # A fresh direct connection rules out ORM state and proxy effects.
            async with direct.connect() as connection:
                reference = await connection.scalar(query)
            committed = failure == "lost-commit-reply"
            assert reference == (expected_reference if committed else old_reference)
            assert objects.exists(old_key)
            assert objects.exists(new_key) is committed
            if committed:
                assert b"".join(objects.iter_range(new_key)) == b"new-file"
        finally:
            try:
                await direct.dispose()
                async with admin.begin() as connection:
                    await connection.execute(
                        text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                    )
            finally:
                await admin.dispose()

    asyncio.run(scenario())

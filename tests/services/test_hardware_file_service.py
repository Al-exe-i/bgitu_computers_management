import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.exceptions import HardwareFileNotFoundError, HardwareNotFoundError
from db.transaction import SessionTransaction
from modules.inventory.services.hardware_files import HardwareFileService
from tests.transaction_helpers import make_transaction_session, transaction_callbacks


class FakeFilesRepo:
    def __init__(self, file_row=None) -> None:
        self.file_row = file_row
        self.created: list[object] = []
        self.deleted: list[int] = []
        self.next_id = 1

    async def get_by_id(self, file_id: int):
        if self.file_row and self.file_row.id == file_id:
            return self.file_row
        return None

    async def create(self, hardware_file):
        hardware_file.id = self.next_id
        self.next_id += 1
        self.created.append(hardware_file)
        return hardware_file

    async def delete(self, file_id: int) -> bool:
        self.deleted.append(file_id)
        return True


class FakeHardwareLookup:
    def __init__(self, hardware=None) -> None:
        self.hardware = hardware or SimpleNamespace(id=9, audience_id=12)
        self.requested_ids: list[int] = []

    async def get(self, hardware_id: int):
        self.requested_ids.append(hardware_id)
        if self.hardware and self.hardware.id == hardware_id:
            return self.hardware
        return None


class FakeStorage:
    def __init__(self) -> None:
        self.saved: list[object] = []
        self.deleted: list[str] = []

    async def save(self, file, *, extension: str) -> str:
        self.saved.append(file)
        return f"uploads/file{extension}"

    def delete(self, file_path: str) -> bool:
        self.deleted.append(file_path)
        return True


class FakeUpload:
    def __init__(self, *, filename: str, content_type: str, size: int = 100) -> None:
        self.filename = filename
        self.content_type = content_type
        self.size = size

    async def read(self, size: int = -1) -> bytes:
        return b""


def test_update_files_stores_only_supported_files() -> None:
    async def scenario() -> None:
        files_repo = FakeFilesRepo()
        storage = FakeStorage()
        session = make_transaction_session()
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
            **transaction_callbacks(session),
        )

        result = await service.update_files(
            9,
            [
                FakeUpload(filename="photo.png", content_type="image/png"),
                FakeUpload(filename="unsafe.svg", content_type="image/svg+xml"),
                FakeUpload(filename="notes.txt", content_type="text/plain"),
                FakeUpload(
                    filename="big.mp4", content_type="video/mp4", size=101 * 1024 * 1024
                ),
            ],
        )

        assert result.audience_id == 12
        assert len(result.files) == 1
        assert result.files[0].file_path == "uploads/file.png"
        assert result.files[0].file_type == "image/png"
        assert [file.filename for file in storage.saved] == ["photo.png"]
        assert len(files_repo.created) == 1
        await SessionTransaction(session).commit()
        assert storage.deleted == []
        assert session.info == {}

    asyncio.run(scenario())


def test_update_files_missing_hardware_raises_application_error() -> None:
    async def scenario() -> None:
        files_repo = FakeFilesRepo()
        storage = FakeStorage()
        hardware = FakeHardwareLookup(SimpleNamespace(id=99, audience_id=12))
        session = make_transaction_session()
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=hardware,
            storage=storage,
            **transaction_callbacks(session),
        )

        with pytest.raises(HardwareNotFoundError):
            await service.update_files(
                9,
                [FakeUpload(filename="photo.png", content_type="image/png")],
            )

        assert hardware.requested_ids == [9]
        assert storage.saved == []
        assert files_repo.created == []

    asyncio.run(scenario())


def test_delete_file_removes_storage_and_record() -> None:
    async def scenario() -> None:
        file_row = SimpleNamespace(
            id=5,
            hardware_id=9,
            file_path="uploads/photo.png",
            file_type="image/png",
        )
        files_repo = FakeFilesRepo(file_row=file_row)
        storage = FakeStorage()
        session = make_transaction_session()
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
            **transaction_callbacks(session),
        )

        result = await service.delete_file(5)

        assert result.audience_id == 12
        assert files_repo.deleted == [5]
        assert storage.deleted == []
        await SessionTransaction(session).commit()
        assert storage.deleted == ["uploads/photo.png"]
        assert session.info == {}

    asyncio.run(scenario())


def test_delete_file_missing_record_raises_application_error() -> None:
    async def scenario() -> None:
        service = HardwareFileService(
            files_repo=FakeFilesRepo(),
            hardware=FakeHardwareLookup(),
            storage=FakeStorage(),
            **transaction_callbacks(make_transaction_session()),
        )

        with pytest.raises(HardwareFileNotFoundError):
            await service.delete_file(404)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "failure",
    [
        "second_upload",
        "second_record",
        "audit",
        "flush",
        "commit",
        "cancel",
        "cancel_commit",
    ],
)
def test_batch_upload_failure_compensates_only_before_commit(failure):
    async def scenario():
        repo = FakeFilesRepo()
        storage = FakeStorage()
        session = make_transaction_session()
        transaction = SessionTransaction(session)
        service = HardwareFileService(
            files_repo=repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
            **transaction_callbacks(session),
        )
        original_save = storage.save

        async def save(file, *, extension):
            if failure == "second_upload" and file.filename == "second.png":
                raise RuntimeError("upload failed")
            await original_save(file, extension=extension)
            return f"uploads/{file.filename}"

        storage.save = save
        if failure == "second_record":
            repo.create = AsyncMock(
                side_effect=[
                    SimpleNamespace(
                        id=1,
                        hardware_id=9,
                        file_type="image/png",
                        file_path="uploads/first.png",
                    ),
                    RuntimeError("record failed"),
                ]
            )
        error = (
            asyncio.CancelledError
            if failure in {"cancel", "cancel_commit"}
            else RuntimeError
        )
        if failure in {"commit", "cancel_commit"}:
            session.commit.side_effect = error("commit failed")
        if failure == "flush":
            session.flush.side_effect = RuntimeError("flush failed")

        with pytest.raises(error):
            try:
                await service.update_files(
                    9,
                    [
                        FakeUpload(filename="first.png", content_type="image/png"),
                        FakeUpload(filename="second.png", content_type="image/png"),
                    ],
                )
                if failure in {"flush", "commit", "cancel_commit"}:
                    await transaction.commit()
                else:
                    raise error("later request failure")
            except BaseException:
                if failure not in {"flush", "commit", "cancel_commit"}:
                    await transaction.rollback()
                raise

        expected = []
        if failure not in {"commit", "cancel_commit"}:
            expected.append("uploads/first.png")
            if failure != "second_upload":
                expected.append("uploads/second.png")
        assert storage.deleted == expected
        assert session.info == {}
        session.rollback.assert_awaited_once()

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["write", "audit", "commit"])
def test_delete_failure_never_removes_the_stored_object(failure):
    async def scenario():
        repo = FakeFilesRepo(
            SimpleNamespace(id=5, hardware_id=9, file_path="uploads/photo.png")
        )
        storage = FakeStorage()
        session = make_transaction_session()
        transaction = SessionTransaction(session)
        service = HardwareFileService(
            files_repo=repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
            **transaction_callbacks(session),
        )
        if failure == "write":
            repo.delete = AsyncMock(side_effect=RuntimeError("delete failed"))
        if failure == "commit":
            session.commit.side_effect = RuntimeError("commit failed")

        with pytest.raises(RuntimeError):
            try:
                await service.delete_file(5)
                if failure == "commit":
                    await transaction.commit()
                else:
                    raise RuntimeError("audit failed")
            except RuntimeError:
                if failure != "commit":
                    await transaction.rollback()
                raise

        assert storage.deleted == []
        assert session.info == {}

    asyncio.run(scenario())

import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import HardwareFileNotFoundError, HardwareNotFoundError
from services.hardware_file_service import HardwareFileService


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

    async def save(self, file) -> str:
        self.saved.append(file)
        return f"uploads/{file.filename}"

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
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
        )

        result = await service.update_files(
            9,
            [
                FakeUpload(filename="photo.png", content_type="image/png"),
                FakeUpload(filename="notes.txt", content_type="text/plain"),
                FakeUpload(filename="big.mp4", content_type="video/mp4", size=21 * 1024 * 1024),
            ],
        )

        assert result.audience_id == 12
        assert len(result.files) == 1
        assert result.files[0].file_path == "uploads/photo.png"
        assert result.files[0].file_type == "image/png"
        assert [file.filename for file in storage.saved] == ["photo.png"]
        assert len(files_repo.created) == 1

    asyncio.run(scenario())


def test_update_files_missing_hardware_raises_application_error() -> None:
    async def scenario() -> None:
        files_repo = FakeFilesRepo()
        storage = FakeStorage()
        hardware = FakeHardwareLookup(SimpleNamespace(id=99, audience_id=12))
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=hardware,
            storage=storage,
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
        service = HardwareFileService(
            files_repo=files_repo,
            hardware=FakeHardwareLookup(),
            storage=storage,
        )

        result = await service.delete_file(5)

        assert result.audience_id == 12
        assert storage.deleted == ["uploads/photo.png"]
        assert files_repo.deleted == [5]

    asyncio.run(scenario())


def test_delete_file_missing_record_raises_application_error() -> None:
    async def scenario() -> None:
        service = HardwareFileService(
            files_repo=FakeFilesRepo(),
            hardware=FakeHardwareLookup(),
            storage=FakeStorage(),
        )

        with pytest.raises(HardwareFileNotFoundError):
            await service.delete_file(404)

    asyncio.run(scenario())

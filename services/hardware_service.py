from typing import Any, Protocol, Sequence

import aiofiles
import uuid
import os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.exceptions import HTTP404
from models import Hardware
from models.hardware_file import HardwareFile
from repositories.hardware_repo import HardwareRepository
from repositories.hw_files_repo import HardwareFilesRepository
from schemas.hardware import HardwareUpdate, HardwareGridItem
from schemas.hardware_file import HardwareFileResponse


class HardwareGridPort(Protocol):
    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]: ...
    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware: ...
    async def delete(self, hardware_id: int) -> None: ...


class HardwareService:
    def __init__(self, repo: HardwareRepository):
        self.repo = repo

    async def get(self, hardware_id: int):
        hardware = await self.repo.get_by_id(hardware_id)
        return hardware

    async def update_status(self, hardware_id: int, schema: HardwareUpdate):
        update_data: dict[str, Any] = schema.model_dump(exclude_unset=True)

        if update_data.get("state"):
            update_data["description"] = None

        updated_hw = await self.repo.update(hardware_id, update_data)
        if not updated_hw:
            raise HTTP404("Hardware not found")
        return updated_hw

    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]:
        return await self.repo.get_by_audience_id(audience_id)

    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware:
        hw = Hardware(**item.model_dump(exclude={"id"}), audience_id=audience_id)
        return await self.repo.create(hw)

    async def delete(self, hardware_id: int) -> None:
        await self.repo.delete(hardware_id)

    async def update_files(
            self,
            hardware_id: int,
            files: list[UploadFile],
            db: AsyncSession,
    ):
        files_repo = HardwareFilesRepository(db)
        created_files: list[HardwareFileResponse] = []
        audience_id = (await self.get(hardware_id)).audience_id

        for file in files:
            if not (file.content_type.startswith("image/") or file.content_type.startswith("video/")):
                continue

            if file.size > 20 * 1024 * 1024:
                continue

            ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4()}{ext}"

            file_path = os.path.join(settings.static.upload_dir, unique_name)

            async with aiofiles.open(file_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)

            db_file = HardwareFile(
                hardware_id=hardware_id,
                file_type=file.content_type,
                file_path=file_path
            )

            created = await files_repo.create(db_file)
            created_files.append(HardwareFileResponse.model_validate(created, from_attributes=True))
            await db.flush()
        return created_files

    async def get_file_for_stream(self, file_id: int):
        repo = HardwareFilesRepository(self.repo.retrieve_session())
        db_file = await repo.get_by_id(file_id)

        if not db_file:
            raise HTTP404("File record not found")

        if not os.path.exists(db_file.file_path):
            raise HTTP404("File missing on disk")

        return db_file

    async def delete_file(self, file_id: int) -> int:
        files_repo = HardwareFilesRepository(self.repo.retrieve_session())

        db_file = await files_repo.get_by_id(file_id)
        if not db_file:
            raise HTTP404("Файл не найден")

        if os.path.exists(db_file.file_path):
            os.remove(db_file.file_path)

        hw = await self.get(db_file.hardware_id)
        audience_id = hw.audience_id

        await files_repo.delete(file_id)

        return audience_id

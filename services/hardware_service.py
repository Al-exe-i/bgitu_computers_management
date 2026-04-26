from typing import Protocol, Sequence

import aiofiles
import uuid
import os
from loguru import logger
from core.config import settings
from core.exceptions import HTTP404
from models import Hardware
from models.hardware_file import HardwareFile
from repositories.hardware_repo import HardwareRepository
from repositories.hw_files_repo import HardwareFilesRepository
from schemas.hardware import HardwareUpdate, HardwareGridItem
from schemas.hardware_file import HardwareFileResponse
from utils.hw_specs import validate_specs


class HardwareGridPort(Protocol):
    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]: ...
    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware: ...
    async def delete(self, hardware_id: int) -> None: ...


class UploadedHardwareFile(Protocol):
    filename: str | None
    content_type: str | None
    size: int | None

    async def read(self, size: int = -1) -> bytes: ...


class HardwareService:
    def __init__(
        self,
        repo: HardwareRepository,
        files_repo: HardwareFilesRepository | None = None,
    ):
        self.repo = repo
        self.files_repo = files_repo

    async def get(self, hardware_id: int):
        hardware = await self.repo.get_by_id(hardware_id)
        return hardware

    async def update(self, hardware_id: int, schema: HardwareUpdate):
        hardware = await self.repo.get_by_id(hardware_id)
        if not hardware:
            raise HTTP404("Hardware not found")

        update_data = schema.model_dump(exclude_unset=True, exclude={'files'})

        target_type = update_data.get("type", hardware.type)

        if "specs" in update_data:
            update_data["specs"] = validate_specs(target_type, update_data["specs"])
        elif "type" in update_data:
            update_data["specs"] = validate_specs(target_type, hardware.specs)

        if update_data.get("state"):
            update_data["description"] = None

        return await self.repo.update(hardware_id, update_data)

    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]:
        return await self.repo.get_by_audience_id(audience_id)

    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware:
        data = item.model_dump(exclude={"id"})
        data["specs"] = validate_specs(item.type, data.get("specs"))
        hw = Hardware(**data, audience_id=audience_id)
        return await self.repo.create(hw)

    async def delete(self, hardware_id: int) -> None:
        await self.repo.delete(hardware_id)

    async def update_files(
        self,
        hardware_id: int,
        files: Sequence[UploadedHardwareFile],
    ):
        files_repo = self._files_repo()
        created_files: list[HardwareFileResponse] = []
        audience_id = (await self.get(hardware_id)).audience_id

        for file in files:
            content_type = file.content_type or ""
            if not (content_type.startswith("image/") or content_type.startswith("video/")):
                logger.warning(
                    "Hardware file skipped due to unsupported content type: hardware_id={} audience_id={} filename={} content_type={}",
                    hardware_id,
                    audience_id,
                    file.filename,
                    content_type,
                )
                continue

            file_size = file.size or 0
            if file_size > 20 * 1024 * 1024:
                logger.warning(
                    "Hardware file skipped due to size limit: hardware_id={} audience_id={} filename={} size={}",
                    hardware_id,
                    audience_id,
                    file.filename,
                    file_size,
                )
                continue

            ext = os.path.splitext(file.filename or "")[1]
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
            logger.info(
                "Hardware file stored: hardware_id={} audience_id={} file_id={} filename={}",
                hardware_id,
                audience_id,
                created.id,
                file.filename,
            )
        return created_files

    async def get_file_for_stream(self, file_id: int):
        db_file = await self._files_repo().get_by_id(file_id)

        if not db_file:
            logger.warning("Hardware file record not found: file_id={}", file_id)
            raise HTTP404("File record not found")

        if not os.path.exists(db_file.file_path):
            logger.warning(
                "Hardware file missing on disk: file_id={} path={}",
                file_id,
                db_file.file_path,
            )
            raise HTTP404("File missing on disk")

        return db_file

    async def delete_file(self, file_id: int) -> int:
        files_repo = self._files_repo()

        db_file = await files_repo.get_by_id(file_id)
        if not db_file:
            logger.warning("Hardware file delete failed: file_id={} not found", file_id)
            raise HTTP404("Файл не найден")

        if os.path.exists(db_file.file_path):
            os.remove(db_file.file_path)
            logger.info(
                "Hardware file removed from disk: file_id={} path={}",
                file_id,
                db_file.file_path,
            )
        else:
            logger.warning(
                "Hardware file missing on disk during delete: file_id={} path={}",
                file_id,
                db_file.file_path,
            )

        hw = await self.get(db_file.hardware_id)
        audience_id = hw.audience_id

        await files_repo.delete(file_id)
        logger.info(
            "Hardware file record deleted: file_id={} hardware_id={} audience_id={}",
            file_id,
            db_file.hardware_id,
            audience_id,
        )

        return audience_id

    def _files_repo(self) -> HardwareFilesRepository:
        if self.files_repo is None:
            raise RuntimeError("Hardware files repository is not configured")
        return self.files_repo

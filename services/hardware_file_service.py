import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import aiofiles
from loguru import logger

from core.exceptions import HardwareFileNotFoundError, HardwareNotFoundError
from models import Hardware
from models.hardware_file import HardwareFile
from repositories.hw_files_repo import HardwareFilesRepository
from schemas.hardware_file import HardwareFileResponse


MAX_HARDWARE_FILE_SIZE_BYTES = 20 * 1024 * 1024
WRITE_CHUNK_SIZE_BYTES = 1024 * 1024


class UploadedHardwareFile(Protocol):
    filename: str | None
    content_type: str | None
    size: int | None

    async def read(self, size: int = -1) -> bytes: ...


class HardwareLookupPort(Protocol):
    async def get(self, hardware_id: int) -> Hardware | None: ...


@dataclass(slots=True, frozen=True)
class HardwareFilesUpdateResult:
    files: list[HardwareFileResponse]
    audience_id: int


@dataclass(slots=True, frozen=True)
class HardwareFileDeleteResult:
    audience_id: int


class HardwareFileStorage:
    def __init__(self, upload_dir: str) -> None:
        self.upload_dir = upload_dir

    async def save(self, file: UploadedHardwareFile) -> str:
        os.makedirs(self.upload_dir, exist_ok=True)

        ext = os.path.splitext(file.filename or "")[1]
        file_path = os.path.join(self.upload_dir, f"{uuid.uuid4()}{ext}")

        async with aiofiles.open(file_path, "wb") as out_file:
            while content := await file.read(WRITE_CHUNK_SIZE_BYTES):
                await out_file.write(content)

        return file_path

    def delete(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False

        os.remove(file_path)
        return True


class HardwareFileService:
    def __init__(
        self,
        *,
        files_repo: HardwareFilesRepository,
        hardware: HardwareLookupPort,
        storage: HardwareFileStorage,
    ) -> None:
        self.files_repo = files_repo
        self.hardware = hardware
        self.storage = storage

    async def update_files(
        self,
        hardware_id: int,
        files: Sequence[UploadedHardwareFile],
    ) -> HardwareFilesUpdateResult:
        hardware = await self.hardware.get(hardware_id)
        if not hardware:
            raise HardwareNotFoundError()

        created_files: list[HardwareFileResponse] = []

        for file in files:
            content_type = file.content_type or ""
            if not self._is_supported_content_type(content_type):
                logger.warning(
                    "Hardware file skipped due to unsupported content type: hardware_id={} audience_id={} filename={} content_type={}",
                    hardware_id,
                    hardware.audience_id,
                    file.filename,
                    content_type,
                )
                continue

            file_size = file.size or 0
            if file_size > MAX_HARDWARE_FILE_SIZE_BYTES:
                logger.warning(
                    "Hardware file skipped due to size limit: hardware_id={} audience_id={} filename={} size={}",
                    hardware_id,
                    hardware.audience_id,
                    file.filename,
                    file_size,
                )
                continue

            file_path = await self.storage.save(file)
            db_file = HardwareFile(
                hardware_id=hardware_id,
                file_type=content_type,
                file_path=file_path,
            )

            created = await self.files_repo.create(db_file)
            created_files.append(HardwareFileResponse.model_validate(created, from_attributes=True))
            logger.info(
                "Hardware file stored: hardware_id={} audience_id={} file_id={} filename={}",
                hardware_id,
                hardware.audience_id,
                created.id,
                file.filename,
            )

        return HardwareFilesUpdateResult(
            files=created_files,
            audience_id=hardware.audience_id,
        )

    async def delete_file(self, file_id: int) -> HardwareFileDeleteResult:
        db_file = await self.files_repo.get_by_id(file_id)
        if not db_file:
            logger.warning("Hardware file delete failed: file_id={} not found", file_id)
            raise HardwareFileNotFoundError()

        hardware = await self.hardware.get(db_file.hardware_id)
        if not hardware:
            raise HardwareNotFoundError()

        if self.storage.delete(db_file.file_path):
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

        await self.files_repo.delete(file_id)
        logger.info(
            "Hardware file record deleted: file_id={} hardware_id={} audience_id={}",
            file_id,
            db_file.hardware_id,
            hardware.audience_id,
        )

        return HardwareFileDeleteResult(audience_id=hardware.audience_id)

    @staticmethod
    def _is_supported_content_type(content_type: str) -> bool:
        return content_type.startswith("image/") or content_type.startswith("video/")

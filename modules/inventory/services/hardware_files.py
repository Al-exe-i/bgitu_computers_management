from collections.abc import Awaitable, Callable, Sequence
from functools import partial
from typing import Any, Protocol

from loguru import logger

from core.exceptions import HardwareFileNotFoundError, HardwareNotFoundError
from modules.inventory.adapters.hardware_storage import HardwareFileStorage
from modules.inventory.constants import MAX_HARDWARE_FILE_SIZE_BYTES
from modules.inventory.contracts import (
    HardwareFileDeleteResult,
    HardwareFilesUpdateResult,
)
from modules.inventory.models.hardware_file import HardwareFile
from modules.inventory.ports import UploadedHardwareFile
from modules.inventory.repositories.hardware_files import HardwareFilesRepository
from modules.inventory.schemas.hardware import HardwareFullResponse
from modules.inventory.schemas.hardware_file import HardwareFileResponse
from utils.media_types import HARDWARE_EXTENSIONS_BY_MEDIA_TYPE, normalize_media_type


class HardwareLookupPort(Protocol):
    async def get(self, hardware_id: int) -> HardwareFullResponse | None: ...


class HardwareFileService:
    def __init__(
        self,
        *,
        files_repo: HardwareFilesRepository,
        hardware: HardwareLookupPort,
        storage: HardwareFileStorage,
        on_commit: Callable[[Callable[[], Any | Awaitable[Any]]], None],
        on_rollback: Callable[[Callable[[], Any | Awaitable[Any]]], None],
    ) -> None:
        self.files_repo = files_repo
        self.hardware = hardware
        self.storage = storage
        self.on_commit = on_commit
        self.on_rollback = on_rollback

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
            content_type = normalize_media_type(file.content_type)
            extension = HARDWARE_EXTENSIONS_BY_MEDIA_TYPE.get(content_type)
            if extension is None:
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

            file_path = await self.storage.save(file, extension=extension)
            self.on_rollback(partial(self.storage.delete, file_path))
            db_file = HardwareFile(
                hardware_id=hardware_id,
                file_type=content_type,
                file_path=file_path,
            )

            created = await self.files_repo.create(db_file)
            created_files.append(
                HardwareFileResponse.model_validate(created, from_attributes=True)
            )
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

        file_path = db_file.file_path
        hardware_id = db_file.hardware_id
        await self.files_repo.delete(file_id)
        self.on_commit(partial(self._delete_stored_file, file_id, file_path))
        logger.info(
            "Hardware file record deleted: file_id={} hardware_id={} audience_id={}",
            file_id,
            hardware_id,
            hardware.audience_id,
        )

        return HardwareFileDeleteResult(audience_id=hardware.audience_id)

    def _delete_stored_file(self, file_id: int, file_path: str) -> None:
        if self.storage.delete(file_path):
            logger.info(
                "Hardware file removed from disk: file_id={} path={}",
                file_id,
                file_path,
            )
        else:
            logger.warning(
                "Hardware file missing on disk during delete: file_id={} path={}",
                file_id,
                file_path,
            )

    @staticmethod
    def _is_supported_content_type(content_type: str) -> bool:
        return normalize_media_type(content_type) in HARDWARE_EXTENSIONS_BY_MEDIA_TYPE

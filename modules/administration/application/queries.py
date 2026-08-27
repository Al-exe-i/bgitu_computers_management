import mimetypes
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath

from loguru import logger

from core.exceptions import (
    ProtectedFileAccessDeniedError,
    ProtectedFileNotFoundError,
)
from modules.administration.ports import AuditLogReaderPort, ProtectedObjectStoragePort
from schemas.audit_log import AuditLogItem, AuditLogListResponse


@dataclass(slots=True, frozen=True)
class ProtectedFile:
    content: Iterator[bytes]
    filename: str
    media_type: str


class AdministrationProtectedFileQueries:
    def __init__(self, storage: ProtectedObjectStoragePort) -> None:
        self.storage = storage

    async def get_file(self, *, file_path: str) -> ProtectedFile:
        object_key = str(PurePosixPath(file_path.replace("\\", "/").lstrip("/")))
        if object_key == ".." or object_key.startswith("../") or "/../" in object_key:
            logger.warning("Protected file path traversal rejected: {}", object_key)
            raise ProtectedFileAccessDeniedError()

        if not self.storage.exists(object_key):
            logger.warning("Protected file not found: {}", object_key)
            raise ProtectedFileNotFoundError()

        filename = PurePosixPath(object_key).name
        media_type, _ = mimetypes.guess_type(filename)
        return ProtectedFile(
            content=self.storage.iter_range(object_key),
            filename=filename,
            media_type=media_type or "application/octet-stream",
        )


class AdministrationAuditLogQueries:
    def __init__(self, service: AuditLogReaderPort) -> None:
        self.service = service

    async def list_entries(
        self,
        *,
        q: str | None,
        user_id: int | None,
        action: str | None,
        entity_type: str | None,
        entity_id: int | None,
        limit: int,
        offset: int,
    ) -> AuditLogListResponse:
        items, total = await self.service.list(
            q=q,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
        return AuditLogListResponse(
            items=[AuditLogItem.model_validate(item) for item in items],
            total=total,
        )

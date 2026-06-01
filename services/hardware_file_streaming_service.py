import mimetypes
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath

from loguru import logger

from core.exceptions import (
    HardwareFileBadRangeError,
    HardwareFileMissingOnDiskError,
    HardwareFileNotFoundError,
    HardwareFileRangeNotSatisfiableError,
    HardwareFileUnsupportedMediaError,
)
from models.hardware_file import HardwareFile
from repositories.hw_files_repo import HardwareFilesRepository
from services.object_storage import ObjectStorage, object_filename


DEFAULT_RANGE_CHUNK_SIZE = 1024 * 1024


@dataclass(slots=True, frozen=True)
class HardwareDownloadFile:
    key: str
    media_type: str
    filename: str
    storage: ObjectStorage

    def iter_file(self) -> Iterator[bytes]:
        return self.storage.iter_range(self.key)


@dataclass(slots=True, frozen=True)
class HardwareVideoStream:
    key: str
    media_type: str
    status_code: int
    headers: dict[str, str]
    start: int
    content_length: int
    storage: ObjectStorage

    def iter_file(self) -> Iterator[bytes]:
        return self.storage.iter_range(
            self.key,
            offset=self.start,
            length=self.content_length,
        )


class HardwareFileStreamingService:
    def __init__(self, files_repo: HardwareFilesRepository, storage: ObjectStorage) -> None:
        self.files_repo = files_repo
        self.storage = storage

    async def get_download(self, file_id: int) -> HardwareDownloadFile:
        db_file = await self._get_existing_file(file_id)
        return HardwareDownloadFile(
            key=db_file.file_path,
            media_type=db_file.file_type,
            filename=object_filename(db_file.file_path),
            storage=self.storage,
        )

    async def prepare_video_stream(
        self,
        *,
        file_id: int,
        range_header: str | None,
    ) -> HardwareVideoStream:
        db_file = await self._get_existing_file(file_id)
        content_type = self._detect_video_content_type(db_file)
        file_size = self.storage.stat(db_file.file_path).size
        start, end = self._parse_range(
            range_header=range_header,
            file_size=file_size,
        )
        content_length = end - start + 1

        return HardwareVideoStream(
            key=db_file.file_path,
            media_type=content_type,
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": content_type,
            },
            start=start,
            content_length=content_length,
            storage=self.storage,
        )

    async def _get_existing_file(self, file_id: int) -> HardwareFile:
        db_file = await self.files_repo.get_by_id(file_id)
        if not db_file:
            logger.warning("Hardware file record not found: file_id={}", file_id)
            raise HardwareFileNotFoundError()

        if not self.storage.exists(db_file.file_path):
            logger.warning(
                "Hardware file missing in storage: file_id={} key={}",
                file_id,
                db_file.file_path,
            )
            raise HardwareFileMissingOnDiskError()

        return db_file

    @staticmethod
    def _detect_video_content_type(db_file: HardwareFile) -> str:
        content_type = db_file.file_type or ""
        if content_type.startswith("video/"):
            return content_type

        mime_type, _ = mimetypes.guess_type(PurePosixPath(db_file.file_path).name)
        if mime_type and mime_type.startswith("video/"):
            return mime_type

        logger.warning(
            "Video stream rejected: file_id={} content_type={} path={}",
            db_file.id,
            db_file.file_type,
            db_file.file_path,
        )
        raise HardwareFileUnsupportedMediaError()

    @staticmethod
    def _parse_range(
        *,
        range_header: str | None,
        file_size: int,
    ) -> tuple[int, int]:
        if file_size <= 0:
            raise HardwareFileRangeNotSatisfiableError()

        if not range_header:
            return 0, file_size - 1

        if not range_header.startswith("bytes="):
            raise HardwareFileBadRangeError()

        range_value = range_header.removeprefix("bytes=")
        parts = range_value.split("-", maxsplit=1)
        if len(parts) != 2:
            raise HardwareFileBadRangeError()

        try:
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else min(start + DEFAULT_RANGE_CHUNK_SIZE - 1, file_size - 1)
        except ValueError:
            raise HardwareFileBadRangeError()

        if start < 0 or end < start or start >= file_size:
            raise HardwareFileRangeNotSatisfiableError()

        return start, min(end, file_size - 1)

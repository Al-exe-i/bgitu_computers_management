from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterator, Protocol

from loguru import logger

from core.exceptions import InvalidUserPhotoError
from services.media_types import (
    IMAGE_EXTENSIONS_BY_MEDIA_TYPE,
    normalize_media_type,
    safe_image_media_type_for_filename,
)
from services.object_storage import ObjectStorage, object_filename


MAX_AVATAR_FILE_SIZE_BYTES = 5 * 1024 * 1024


class UploadedAvatarFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...
    async def close(self) -> None: ...


@dataclass(slots=True, frozen=True)
class StoredAvatarFile:
    key: str
    media_type: str
    filename: str
    storage: ObjectStorage

    def iter_file(self) -> Iterator[bytes]:
        return self.storage.iter_range(self.key)


class AvatarStorage:
    def __init__(self, storage: ObjectStorage, *, prefix: str = "avatars") -> None:
        self.storage = storage
        self.prefix = prefix

    def get_existing(self, filename: str | None) -> StoredAvatarFile | None:
        if not filename:
            return None

        key = self._key_for_filename(filename)
        if not self.storage.exists(key):
            return None

        media_type = safe_image_media_type_for_filename(object_filename(key))
        if media_type is None:
            logger.warning("Rejected unsafe stored avatar filename={}", filename)
            return None

        return StoredAvatarFile(
            key=key,
            media_type=media_type,
            filename=object_filename(key),
            storage=self.storage,
        )

    async def save(self, file: UploadedAvatarFile) -> str:
        media_type = normalize_media_type(file.content_type)
        extension = IMAGE_EXTENSIONS_BY_MEDIA_TYPE.get(media_type)
        if extension is None:
            raise InvalidUserPhotoError()

        key = await self.storage.save_upload(
            file,
            prefix=self.prefix,
            extension=extension,
            max_size_bytes=MAX_AVATAR_FILE_SIZE_BYTES,
        )
        return object_filename(key)

    def delete(self, filename: str | None) -> bool:
        if not filename:
            return False

        try:
            return self.storage.delete(self._key_for_filename(filename))
        except Exception as exc:
            logger.error("Failed to remove avatar file filename={} error={}", filename, exc)
            return False

    def _key_for_filename(self, filename: str) -> str:
        safe_filename = PurePosixPath(filename.replace("\\", "/")).name
        return str(PurePosixPath(self.prefix.strip("/")) / safe_filename)

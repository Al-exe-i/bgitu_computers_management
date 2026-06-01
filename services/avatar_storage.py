import mimetypes
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterator, Protocol

from loguru import logger

from services.object_storage import ObjectStorage, object_filename


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

        media_type, _ = mimetypes.guess_type(object_filename(key))
        return StoredAvatarFile(
            key=key,
            media_type=media_type or "image/*",
            filename=object_filename(key),
            storage=self.storage,
        )

    async def save(self, file: UploadedAvatarFile) -> str:
        key = await self.storage.save_upload(file, prefix=self.prefix)
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

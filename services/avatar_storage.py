import mimetypes
import os
import uuid
from dataclasses import dataclass
from typing import Protocol

import aiofiles
from loguru import logger


class UploadedAvatarFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...
    async def close(self) -> None: ...


@dataclass(slots=True, frozen=True)
class StoredAvatarFile:
    path: str
    media_type: str


class AvatarStorage:
    def __init__(self, avatars_dir: str) -> None:
        self.avatars_dir = avatars_dir

    def get_existing(self, filename: str | None) -> StoredAvatarFile | None:
        if not filename:
            return None

        path = os.path.join(self.avatars_dir, filename)
        if not os.path.exists(path):
            return None

        media_type, _ = mimetypes.guess_type(path)
        return StoredAvatarFile(path=path, media_type=media_type or "image/*")

    async def save(self, file: UploadedAvatarFile) -> str:
        os.makedirs(self.avatars_dir, exist_ok=True)

        file_ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(self.avatars_dir, unique_filename)

        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                content = await file.read()
                await buffer.write(content)
        finally:
            await file.close()

        return unique_filename

    def delete(self, filename: str | None) -> bool:
        if not filename:
            return False

        file_path = os.path.join(self.avatars_dir, filename)
        if not os.path.exists(file_path):
            return False

        try:
            os.remove(file_path)
        except OSError as exc:
            logger.error("Failed to remove avatar file path={} error={}", file_path, exc)
            return False

        return True

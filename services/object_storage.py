import asyncio
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterator, Protocol

from loguru import logger
from minio import Minio
from minio.error import S3Error


READ_CHUNK_SIZE_BYTES = 64 * 1024
WRITE_CHUNK_SIZE_BYTES = 1024 * 1024


class UploadedObjectFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...


@dataclass(slots=True, frozen=True)
class ObjectStat:
    size: int
    content_type: str | None = None


class ObjectStorage(Protocol):
    async def save_upload(self, file: UploadedObjectFile, *, prefix: str) -> str: ...

    def delete(self, key: str) -> bool: ...

    def exists(self, key: str) -> bool: ...

    def stat(self, key: str) -> ObjectStat: ...

    def iter_range(self, key: str, *, offset: int = 0, length: int | None = None) -> Iterator[bytes]: ...


def build_object_key(*, prefix: str, filename: str | None) -> str:
    suffix = Path(filename or "").suffix
    safe_prefix = prefix.strip("/")
    return str(PurePosixPath(safe_prefix) / f"{uuid.uuid4()}{suffix}")


def object_filename(key: str) -> str:
    return PurePosixPath(key.replace("\\", "/")).name


class LocalObjectStorage:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)

    async def save_upload(self, file: UploadedObjectFile, *, prefix: str) -> str:
        key = build_object_key(prefix=prefix, filename=file.filename)
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import aiofiles

            async with aiofiles.open(path, "wb") as out_file:
                while content := await file.read(WRITE_CHUNK_SIZE_BYTES):
                    await out_file.write(content)
        finally:
            close = getattr(file, "close", None)
            if callable(close):
                await close()

        return key

    def delete(self, key: str) -> bool:
        path = self._path_for_key(key)
        if not path.exists():
            return False

        path.unlink()
        return True

    def exists(self, key: str) -> bool:
        return self._path_for_key(key).is_file()

    def stat(self, key: str) -> ObjectStat:
        path = self._path_for_key(key)
        if not path.is_file():
            raise FileNotFoundError(key)

        return ObjectStat(size=path.stat().st_size, content_type=None)

    def iter_range(self, key: str, *, offset: int = 0, length: int | None = None) -> Iterator[bytes]:
        path = self._path_for_key(key)
        with path.open("rb") as file:
            file.seek(offset)
            remaining = length
            while remaining is None or remaining > 0:
                chunk_size = READ_CHUNK_SIZE_BYTES if remaining is None else min(READ_CHUNK_SIZE_BYTES, remaining)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                if remaining is not None:
                    remaining -= len(chunk)

    def _path_for_key(self, key: str) -> Path:
        candidate = Path(key)
        normalized_key = key.replace("\\", "/")
        normalized_root = str(self.root_dir).replace("\\", "/").rstrip("/")

        if candidate.is_absolute() or normalized_key.startswith(f"{normalized_root}/"):
            path = candidate
        else:
            path = self.root_dir / normalized_key

        resolved = path.resolve()
        root = self.root_dir.resolve()

        try:
            resolved.relative_to(root)
        except ValueError as exc:
            logger.warning("Local storage path traversal attempt: key={} resolved={}", key, resolved)
            raise FileNotFoundError(key) from exc

        return resolved


class MinioObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
    ) -> None:
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket_checked = False

    async def save_upload(self, file: UploadedObjectFile, *, prefix: str) -> str:
        key = build_object_key(prefix=prefix, filename=file.filename)
        content_type = file.content_type or "application/octet-stream"

        try:
            with tempfile.SpooledTemporaryFile(max_size=WRITE_CHUNK_SIZE_BYTES * 8) as buffer:
                size = 0
                while content := await file.read(WRITE_CHUNK_SIZE_BYTES):
                    size += len(content)
                    buffer.write(content)

                buffer.seek(0)
                await asyncio.to_thread(
                    self._put_object,
                    key,
                    buffer,
                    size,
                    content_type,
                )
        finally:
            close = getattr(file, "close", None)
            if callable(close):
                await close()

        return key

    def delete(self, key: str) -> bool:
        try:
            self.client.remove_object(self.bucket_name, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchBucket"}:
                return False
            raise

        return True

    def exists(self, key: str) -> bool:
        try:
            self.stat(key)
        except FileNotFoundError:
            return False

        return True

    def stat(self, key: str) -> ObjectStat:
        try:
            stat = self.client.stat_object(self.bucket_name, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchBucket"}:
                raise FileNotFoundError(key) from exc
            raise

        return ObjectStat(
            size=stat.size or 0,
            content_type=stat.content_type,
        )

    def iter_range(self, key: str, *, offset: int = 0, length: int | None = None) -> Iterator[bytes]:
        kwargs = {"offset": offset}
        if length is not None:
            kwargs["length"] = length

        response = self.client.get_object(self.bucket_name, key, **kwargs)
        try:
            yield from response.stream(READ_CHUNK_SIZE_BYTES)
        finally:
            response.close()
            response.release_conn()

    def _ensure_bucket(self) -> None:
        if self._bucket_checked:
            return

        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

        self._bucket_checked = True

    def _put_object(self, key: str, buffer, size: int, content_type: str) -> None:
        self._ensure_bucket()
        self.client.put_object(
            self.bucket_name,
            key,
            buffer,
            length=size,
            content_type=content_type,
        )

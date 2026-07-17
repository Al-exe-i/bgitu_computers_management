import asyncio

import pytest

from core.exceptions import UploadTooLargeError
from services.object_storage import LocalObjectStorage


class ChunkedUpload:
    def __init__(self, chunks: list[bytes], filename: str = "payload.html") -> None:
        self.chunks = list(chunks)
        self.filename = filename
        self.content_type = "image/png"
        self.closed = False

    async def read(self, size: int = -1) -> bytes:
        return self.chunks.pop(0) if self.chunks else b""

    async def close(self) -> None:
        self.closed = True


def test_local_storage_enforces_stream_limit_and_removes_partial_file(tmp_path) -> None:
    async def scenario() -> None:
        storage = LocalObjectStorage(tmp_path)
        upload = ChunkedUpload([b"1234", b"5678"])

        with pytest.raises(UploadTooLargeError):
            await storage.save_upload(
                upload,
                prefix="avatars",
                extension=".png",
                max_size_bytes=6,
            )

        assert upload.closed is True
        assert not any(path.is_file() for path in tmp_path.rglob("*"))

    asyncio.run(scenario())


def test_local_storage_uses_server_selected_extension(tmp_path) -> None:
    async def scenario() -> None:
        storage = LocalObjectStorage(tmp_path)
        upload = ChunkedUpload([b"png-data"])

        key = await storage.save_upload(
            upload,
            prefix="avatars",
            extension=".png",
            max_size_bytes=1024,
        )

        assert key.startswith("avatars/")
        assert key.endswith(".png")
        assert not key.endswith(".html")

    asyncio.run(scenario())

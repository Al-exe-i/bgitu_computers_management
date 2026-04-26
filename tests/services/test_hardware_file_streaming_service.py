import asyncio
import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.exceptions import (
    HardwareFileBadRangeError,
    HardwareFileUnsupportedMediaError,
)
from services.hardware_file_streaming_service import HardwareFileStreamingService


class FakeHardwareFilesRepo:
    def __init__(self, files: dict[int, SimpleNamespace]) -> None:
        self.files = files

    async def get_by_id(self, file_id: int):
        return self.files.get(file_id)


def make_service(row: SimpleNamespace) -> HardwareFileStreamingService:
    return HardwareFileStreamingService(FakeHardwareFilesRepo({row.id: row}))


class BytesFile(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


def test_get_download_returns_file_response_data() -> None:
    async def scenario() -> None:
        service = make_service(
            SimpleNamespace(id=1, file_path="uploads/manual.pdf", file_type="application/pdf")
        )

        with patch("services.hardware_file_streaming_service.os.path.exists", return_value=True):
            result = await service.get_download(1)

        assert result.path == "uploads/manual.pdf"
        assert result.media_type == "application/pdf"
        assert result.filename == "manual.pdf"

    asyncio.run(scenario())


def test_prepare_video_stream_parses_range_and_streams_requested_bytes() -> None:
    async def scenario() -> None:
        service = make_service(SimpleNamespace(id=1, file_path="uploads/video.mp4", file_type="video/mp4"))

        with (
            patch("services.hardware_file_streaming_service.os.path.exists", return_value=True),
            patch("services.hardware_file_streaming_service.os.path.getsize", return_value=10),
        ):
            result = await service.prepare_video_stream(file_id=1, range_header="bytes=2-5")

        assert result.status_code == 206
        assert result.media_type == "video/mp4"
        assert result.headers["Content-Range"] == "bytes 2-5/10"
        assert result.headers["Content-Length"] == "4"
        with patch("builtins.open", return_value=BytesFile(b"0123456789")):
            assert b"".join(result.iter_file()) == b"2345"

    asyncio.run(scenario())


def test_prepare_video_stream_detects_video_by_file_extension() -> None:
    async def scenario() -> None:
        service = make_service(
            SimpleNamespace(id=1, file_path="uploads/video.mp4", file_type="application/octet-stream")
        )

        with (
            patch("services.hardware_file_streaming_service.os.path.exists", return_value=True),
            patch("services.hardware_file_streaming_service.os.path.getsize", return_value=10),
        ):
            result = await service.prepare_video_stream(file_id=1, range_header=None)

        assert result.media_type == "video/mp4"
        assert result.headers["Content-Range"] == "bytes 0-9/10"

    asyncio.run(scenario())


def test_prepare_video_stream_rejects_bad_range_header() -> None:
    async def scenario() -> None:
        service = make_service(SimpleNamespace(id=1, file_path="uploads/video.mp4", file_type="video/mp4"))

        with (
            patch("services.hardware_file_streaming_service.os.path.exists", return_value=True),
            patch("services.hardware_file_streaming_service.os.path.getsize", return_value=10),
            pytest.raises(HardwareFileBadRangeError),
        ):
            await service.prepare_video_stream(file_id=1, range_header="bytes=bad")

    asyncio.run(scenario())


def test_prepare_video_stream_rejects_non_video_file() -> None:
    async def scenario() -> None:
        service = make_service(SimpleNamespace(id=1, file_path="uploads/notes.txt", file_type="text/plain"))

        with (
            patch("services.hardware_file_streaming_service.os.path.exists", return_value=True),
            pytest.raises(HardwareFileUnsupportedMediaError),
        ):
            await service.prepare_video_stream(file_id=1, range_header=None)

    asyncio.run(scenario())

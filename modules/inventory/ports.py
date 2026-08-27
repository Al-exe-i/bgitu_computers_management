from collections.abc import Iterator, Sequence
from typing import Any, Protocol
from uuid import UUID

from schemas.analytics import (
    HardwareAnalyticsFilterOptions,
    HardwareAnalyticsFilters,
    HardwareAnalyticsResponse,
)
from schemas.audience import (
    AudienceCreate,
    AudienceResponse,
    AudienceShortResponse,
    AudienceUpdate,
)
from schemas.hardware import HardwareUpdate
from schemas.hardware_file import HardwareFileResponse
from schemas.office import OfficeCreate, OfficeResponse, OfficeShort, OfficeUpdate
from schemas.spec_template import SpecTemplateCreate, SpecTemplateUpdate


class AuditLogger(Protocol):
    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ) -> Any: ...


class InventoryActor(Protocol):
    id: int
    role: object
    is_superuser: bool


class UploadedHardwareFile(Protocol):
    filename: str | None
    content_type: str | None
    size: int | None

    async def read(self, size: int = -1) -> bytes: ...


class HardwareFilesUpdateResult(Protocol):
    files: list[HardwareFileResponse]
    audience_id: int


class HardwareFileDeleteResult(Protocol):
    audience_id: int


class AudienceServicePort(Protocol):
    async def get_list(self) -> Sequence[AudienceResponse]: ...
    async def get_one(self, audience_id: int) -> AudienceResponse: ...
    async def get_one_by_public_id(self, public_id: UUID) -> AudienceResponse: ...
    async def create_audience(self, schema: AudienceCreate) -> AudienceShortResponse: ...
    async def update_audience(self, audience_id: int, schema: AudienceUpdate) -> AudienceShortResponse: ...
    async def update_audience_by_public_id(self, public_id: UUID, schema: AudienceUpdate) -> AudienceShortResponse: ...
    async def delete_audience(self, audience_id: int) -> None: ...
    async def delete_audience_by_public_id(self, public_id: UUID) -> None: ...


class OfficeServicePort(Protocol):
    async def get_all(self) -> Sequence[OfficeResponse | OfficeShort]: ...
    async def get_all_short(self) -> Sequence[OfficeShort]: ...
    async def get(self, office_id: int) -> OfficeResponse | None: ...
    async def create(self, office: OfficeCreate) -> Any: ...
    async def update(self, office_id: int, schema: OfficeUpdate) -> Any | None: ...
    async def delete(self, office_id: int) -> bool: ...


class HardwareServicePort(Protocol):
    async def get(self, hardware_id: int) -> Any | None: ...
    async def update(self, hardware_id: int, data: HardwareUpdate) -> Any: ...


class HardwareFileServicePort(Protocol):
    async def update_files(
        self,
        hardware_id: int,
        files: Sequence[UploadedHardwareFile],
    ) -> HardwareFilesUpdateResult: ...

    async def delete_file(self, file_id: int) -> HardwareFileDeleteResult: ...


class DownloadableHardwareFile(Protocol):
    media_type: str
    filename: str

    def iter_file(self) -> Iterator[bytes]: ...


class StreamableHardwareVideo(Protocol):
    media_type: str
    status_code: int
    headers: dict[str, str]

    def iter_file(self) -> Iterator[bytes]: ...


class HardwareFileStreamingServicePort(Protocol):
    async def get_download(self, file_id: int) -> DownloadableHardwareFile: ...

    async def prepare_video_stream(
        self,
        *,
        file_id: int,
        range_header: str | None,
    ) -> StreamableHardwareVideo: ...


class SpecTemplateServicePort(Protocol):
    async def list(self, hardware_type: Any | None = None) -> Sequence[Any]: ...
    async def get(self, template_id: int) -> Any | None: ...
    async def create(self, data: SpecTemplateCreate) -> Any: ...
    async def update(self, template_id: int, data: SpecTemplateUpdate) -> Any | None: ...
    async def delete(self, template_id: int) -> bool: ...


class HardwareAnalyticsServicePort(Protocol):
    async def get_hardware(
        self,
        filters: HardwareAnalyticsFilters,
    ) -> HardwareAnalyticsResponse: ...

    async def get_filter_options(self) -> HardwareAnalyticsFilterOptions: ...

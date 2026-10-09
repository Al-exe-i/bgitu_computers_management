from collections.abc import Iterator, Sequence
from typing import Protocol
from uuid import UUID

from modules.identity.public import UserRole
from modules.inventory.contracts import (
    HardwareFileDeleteResult,
    HardwareFilesUpdateResult,
)
from modules.inventory.schemas.analytics import (
    HardwareAnalyticsFilterOptions,
    HardwareAnalyticsFilters,
    HardwareAnalyticsResponse,
)
from modules.inventory.schemas.audience import (
    AudienceCreate,
    AudienceResponse,
    AudienceShortResponse,
    AudienceUpdate,
)
from modules.inventory.schemas.hardware import HardwareFullResponse, HardwareUpdate
from modules.inventory.schemas.office import (
    OfficeCreate,
    OfficeResponse,
    OfficeShort,
    OfficeUpdate,
)
from modules.inventory.schemas.spec_template import (
    SpecTemplateCreate,
    SpecTemplateResponse,
    SpecTemplateUpdate,
)
from modules.inventory.types import HardwareType


class InventoryActor(Protocol):
    id: int
    role: UserRole
    is_superuser: bool


class UploadedHardwareFile(Protocol):
    filename: str | None
    content_type: str | None
    size: int | None

    async def read(self, size: int = -1) -> bytes: ...


class AudienceServicePort(Protocol):
    async def get_list(self) -> Sequence[AudienceResponse]: ...
    async def get_one(self, audience_id: int) -> AudienceResponse: ...
    async def get_one_by_public_id(self, public_id: UUID) -> AudienceResponse: ...
    async def create_audience(
        self, schema: AudienceCreate
    ) -> AudienceShortResponse: ...
    async def update_audience(
        self, audience_id: int, schema: AudienceUpdate
    ) -> AudienceShortResponse: ...
    async def update_audience_by_public_id(
        self, public_id: UUID, schema: AudienceUpdate
    ) -> AudienceShortResponse: ...
    async def delete_audience(self, audience_id: int) -> None: ...
    async def delete_audience_by_public_id(self, public_id: UUID) -> None: ...


class OfficeServicePort(Protocol):
    async def get_all(self) -> Sequence[OfficeResponse | OfficeShort]: ...
    async def get_all_short(self) -> Sequence[OfficeShort]: ...
    async def get(self, office_id: int) -> OfficeResponse | None: ...
    async def create(self, office: OfficeCreate) -> OfficeShort: ...
    async def update(
        self, office_id: int, schema: OfficeUpdate
    ) -> OfficeShort | None: ...
    async def delete(self, office_id: int) -> bool: ...


class HardwareServicePort(Protocol):
    async def get(self, hardware_id: int) -> HardwareFullResponse | None: ...
    async def update(
        self, hardware_id: int, data: HardwareUpdate
    ) -> HardwareFullResponse: ...


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
    async def list(
        self, hardware_type: HardwareType | None = None
    ) -> Sequence[SpecTemplateResponse]: ...
    async def get(self, template_id: int) -> SpecTemplateResponse | None: ...
    async def create(self, data: SpecTemplateCreate) -> SpecTemplateResponse: ...
    async def update(
        self, template_id: int, data: SpecTemplateUpdate
    ) -> SpecTemplateResponse | None: ...
    async def delete(self, template_id: int) -> bool: ...


class HardwareAnalyticsServicePort(Protocol):
    async def get_hardware(
        self,
        filters: HardwareAnalyticsFilters,
    ) -> HardwareAnalyticsResponse: ...

    async def get_filter_options(self) -> HardwareAnalyticsFilterOptions: ...

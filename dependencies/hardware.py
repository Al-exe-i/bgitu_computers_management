from typing import Annotated

from fastapi import Depends

from core.config import settings
from dependencies.cache import office_short_list_cache_dep
from db.session import session_dep
from repositories.hardware_repo import HardwareRepository
from repositories.hw_files_repo import HardwareFilesRepository
from services.hardware_file_service import HardwareFileService, HardwareFileStorage
from services.hardware_file_streaming_service import HardwareFileStreamingService
from services.hardware_service import HardwareService


async def get_hardware_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
) -> HardwareService:
    return HardwareService(HardwareRepository(db), office_short_cache)

hardware_service_dep = Annotated[HardwareService, Depends(get_hardware_service)]


async def get_hardware_file_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
) -> HardwareFileService:
    return HardwareFileService(
        files_repo=HardwareFilesRepository(db),
        hardware=HardwareService(HardwareRepository(db), office_short_cache),
        storage=HardwareFileStorage(settings.static.upload_dir),
    )


hardware_file_service_dep = Annotated[
    HardwareFileService,
    Depends(get_hardware_file_service),
]


async def get_hardware_file_streaming_service(db: session_dep) -> HardwareFileStreamingService:
    return HardwareFileStreamingService(HardwareFilesRepository(db))


hardware_file_streaming_service_dep = Annotated[
    HardwareFileStreamingService,
    Depends(get_hardware_file_streaming_service),
]

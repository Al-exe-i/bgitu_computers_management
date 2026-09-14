from functools import partial
from typing import Annotated

from fastapi import Depends

from db.post_commit import add_post_commit_hook
from db.session import session_dep
from dependencies.cache import office_short_list_cache_dep
from dependencies.storage import object_storage_dep
from modules.inventory.adapters.hardware_storage import HardwareFileStorage
from modules.inventory.repositories.hardware import HardwareRepository
from modules.inventory.repositories.hardware_files import HardwareFilesRepository
from modules.inventory.services.file_streaming import HardwareFileStreamingService
from modules.inventory.services.hardware import HardwareService
from modules.inventory.services.hardware_files import HardwareFileService


async def get_hardware_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
) -> HardwareService:
    return HardwareService(HardwareRepository(db), office_short_cache, on_commit=partial(add_post_commit_hook, db))

hardware_service_dep = Annotated[HardwareService, Depends(get_hardware_service)]


async def get_hardware_file_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
    storage: object_storage_dep,
) -> HardwareFileService:
    return HardwareFileService(
        files_repo=HardwareFilesRepository(db),
        hardware=HardwareService(HardwareRepository(db), office_short_cache, on_commit=partial(add_post_commit_hook, db)),
        storage=HardwareFileStorage(storage),
    )


hardware_file_service_dep = Annotated[
    HardwareFileService,
    Depends(get_hardware_file_service),
]


async def get_hardware_file_streaming_service(
    db: session_dep,
    storage: object_storage_dep,
) -> HardwareFileStreamingService:
    return HardwareFileStreamingService(HardwareFilesRepository(db), storage)


hardware_file_streaming_service_dep = Annotated[
    HardwareFileStreamingService,
    Depends(get_hardware_file_streaming_service),
]

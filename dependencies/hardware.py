from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.hardware_repo import HardwareRepository
from repositories.hw_files_repo import HardwareFilesRepository
from services.hardware_service import HardwareService


async def get_hardware_service(db: session_dep) -> HardwareService:
    service = HardwareService(
        HardwareRepository(db),
        HardwareFilesRepository(db),
    )
    return service

hardware_service_dep = Annotated[HardwareService, Depends(get_hardware_service)]

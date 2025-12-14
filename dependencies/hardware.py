from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.hardware_repo import HardwareRepository
from services.hardware_service import HardwareService


async def get_hardware_service(db: session_dep) -> HardwareService:
    repo = HardwareRepository(db)
    service = HardwareService(repo)
    return service

hardware_service_dep = Annotated[HardwareService, Depends(get_hardware_service)]
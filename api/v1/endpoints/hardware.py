from fastapi import APIRouter

from dependencies.hardware import hardware_service_dep
from schemas.hardware import HardwareResponse, HardwareUpdate

router = APIRouter()

@router.patch("/{hardware_id}", response_model=HardwareResponse)
async def update_hardware_status(
    hardware_id: int,
    data: HardwareUpdate,
    service: hardware_service_dep
):
    """
    Обновить статус, комментарий или позицию конкретного оборудования.
    Используется при клике 'Исправно/Неисправно' или перемещении на фронте.
    """
    return await service.update_status(hardware_id, data)
from fastapi import APIRouter, UploadFile
from core.exceptions import HTTP404
from db.session import session_dep
from dependencies.auth import admin_dep
from dependencies.hardware import hardware_service_dep
from schemas.hardware import HardwareFullResponse, HardwareUpdate
from fastapi.responses import FileResponse
import os

from schemas.hardware_file import HardwareFileResponse

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
        hardware_id: int,
        files: list[UploadFile],
        service: hardware_service_dep,
        db: session_dep
):
    hardware = await service.get(hardware_id)
    if not hardware:
        raise HTTP404("Hardware doesn't exist")
    result: list[HardwareFileResponse] = await service.update_files(hardware_id, files, db)
    return {"status": "success", "files": result}


@router.patch("/{hardware_id}", response_model=HardwareFullResponse)
async def update_hardware_status(
        hardware_id: int,
        data: HardwareUpdate,
        service: hardware_service_dep,
        user: admin_dep
):
    """
    Обновить статус, комментарий или позицию конкретного оборудования.
    Используется при клике 'Исправно/Неисправно' или перемещении на фронте.
    """
    return await service.update_status(hardware_id, data)


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    service: hardware_service_dep
):
    db_file = await service.get_file_for_stream(file_id)

    filename = os.path.basename(db_file.file_path)

    return FileResponse(
        path=db_file.file_path,
        media_type=db_file.file_type,
        filename=filename
    )


@router.delete("/files/{file_id}")
async def delete_hardware_file(
    file_id: int,
    service: hardware_service_dep
):
    await service.delete_file(file_id)
    return {"status": "success"}
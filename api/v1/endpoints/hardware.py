from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from core.exceptions import (
    HTTP403,
    HTTP404,
    HardwareFileBadRangeError,
    HardwareFileMissingOnDiskError,
    HardwareFileNotFoundError,
    HardwareFileRangeNotSatisfiableError,
    HardwareFileUnsupportedMediaError,
    HardwareNotFoundError,
    HardwarePermissionDeniedError,
)
from dependencies.audit_actor import admin_audit_actor_dep, user_audit_actor_dep
from dependencies.auth import user_dep
from dependencies.hardware import hardware_file_streaming_service_dep
from dependencies.inventory import inventory_hardware_use_cases_dep
from dependencies.realtime import realtime_dep
from schemas.hardware import HardwareFullResponse, HardwareUpdate
from modules.inventory.adapters.fastapi_events import dispatch_inventory_events

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
    hardware_id: int,
    files: list[UploadFile],
    use_cases: inventory_hardware_use_cases_dep,
    background_tasks: BackgroundTasks,
    audit: admin_audit_actor_dep,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.add_files(
            hardware_id=hardware_id,
            files=files,
            audit=audit,
        )
    except HardwareNotFoundError:
        raise HTTP404("Hardware doesn't exist")

    dispatch_inventory_events(background_tasks, realtime, result.events)
    return {"status": "success", "files": result.files}


@router.patch("/{hardware_id}", response_model=HardwareFullResponse)
async def update_hardware(
    hardware_id: int,
    data: HardwareUpdate,
    use_cases: inventory_hardware_use_cases_dep,
    background_tasks: BackgroundTasks,
    audit: user_audit_actor_dep,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.update_hardware(
            hardware_id=hardware_id,
            data=data,
            actor=audit.user,
            audit=audit,
        )
    except HardwareNotFoundError:
        raise HTTP404("Hardware not found")
    except HardwarePermissionDeniedError as exc:
        raise HTTP403(str(exc) or exc.detail)

    dispatch_inventory_events(background_tasks, realtime, result.events)
    return result.hardware


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    service: hardware_file_streaming_service_dep,
    user: user_dep,
):
    try:
        file = await service.get_download(file_id)
    except (HardwareFileNotFoundError, HardwareFileMissingOnDiskError) as exc:
        raise HTTP404(exc.detail)

    return FileResponse(
        path=file.path,
        media_type=file.media_type,
        filename=file.filename,
    )


@router.get("/stream/{file_id}")
async def stream_video(
    file_id: int,
    request: Request,
    service: hardware_file_streaming_service_dep,
    user: user_dep,
):
    try:
        stream = await service.prepare_video_stream(
            file_id=file_id,
            range_header=request.headers.get("Range"),
        )
    except (HardwareFileNotFoundError, HardwareFileMissingOnDiskError) as exc:
        raise HTTP404(exc.detail)
    except HardwareFileUnsupportedMediaError as exc:
        raise HTTPException(status_code=415, detail=exc.detail)
    except HardwareFileBadRangeError as exc:
        raise HTTPException(status_code=400, detail=exc.detail)
    except HardwareFileRangeNotSatisfiableError as exc:
        raise HTTPException(status_code=416, detail=exc.detail)

    return StreamingResponse(
        stream.iter_file(),
        status_code=stream.status_code,
        headers=stream.headers,
        media_type=stream.media_type,
    )


@router.delete("/files/{file_id}")
async def delete_hardware_file(
    file_id: int,
    use_cases: inventory_hardware_use_cases_dep,
    background_tasks: BackgroundTasks,
    audit: admin_audit_actor_dep,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.delete_file(
            file_id=file_id,
            audit=audit,
        )
    except (HardwareFileNotFoundError, HardwareNotFoundError) as exc:
        raise HTTP404(exc.detail)

    dispatch_inventory_events(background_tasks, realtime, result.events)
    return {"status": "success"}

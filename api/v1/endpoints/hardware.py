from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from api.v1.application_events import dispatch_result_events
from dependencies.audit_actor import admin_audit_actor_dep, user_audit_actor_dep
from dependencies.auth import user_dep
from dependencies.events import inventory_event_dispatcher_dep
from dependencies.hardware import hardware_file_streaming_service_dep
from dependencies.inventory import inventory_hardware_use_cases_dep
from schemas.hardware import HardwareFullResponse, HardwareUpdate

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
    hardware_id: int,
    files: list[UploadFile],
    use_cases: inventory_hardware_use_cases_dep,
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    result = await dispatch_result_events(
        await use_cases.add_files(
            hardware_id=hardware_id,
            files=files,
            audit=audit,
        ),
        events,
    )

    return {"status": "success", "files": result.files}


@router.patch("/{hardware_id}", response_model=HardwareFullResponse)
async def update_hardware(
    hardware_id: int,
    data: HardwareUpdate,
    use_cases: inventory_hardware_use_cases_dep,
    audit: user_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    result = await dispatch_result_events(
        await use_cases.update_hardware(
            hardware_id=hardware_id,
            data=data,
            actor=audit.user,
            audit=audit,
        ),
        events,
    )

    return result.hardware


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    service: hardware_file_streaming_service_dep,
    user: user_dep,
):
    file = await service.get_download(file_id)

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
    stream = await service.prepare_video_stream(
        file_id=file_id,
        range_header=request.headers.get("Range"),
    )

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
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    result = await dispatch_result_events(
        await use_cases.delete_file(
            file_id=file_id,
            audit=audit,
        ),
        events,
    )

    return {"status": "success"}

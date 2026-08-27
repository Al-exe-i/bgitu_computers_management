from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import StreamingResponse

from api.v1.application_events import dispatch_result_events
from dependencies.audit_actor import admin_audit_actor_dep, user_audit_actor_dep
from dependencies.auth import user_dep
from dependencies.events import inventory_event_dispatcher_dep
from dependencies.inventory import (
    inventory_hardware_file_queries_dep,
    inventory_hardware_use_cases_dep,
)
from schemas.hardware import HardwareFullResponse, HardwareUpdate
from utils.file_responses import secure_file_headers

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
    hardware_id: int,
    files: list[UploadFile],
    use_cases: inventory_hardware_use_cases_dep,
    audit: user_audit_actor_dep,
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
    queries: inventory_hardware_file_queries_dep,
    user: user_dep,
):
    file = await queries.get_download(file_id=file_id)

    return StreamingResponse(
        file.iter_file(),
        media_type=file.media_type,
        headers=secure_file_headers(
            file.filename,
            as_attachment=file.media_type == "application/pdf",
        ),
    )


@router.get("/stream/{file_id}")
async def stream_video(
    file_id: int,
    request: Request,
    queries: inventory_hardware_file_queries_dep,
    user: user_dep,
):
    stream = await queries.prepare_video_stream(
        file_id=file_id,
        range_header=request.headers.get("Range"),
    )

    return StreamingResponse(
        stream.iter_file(),
        status_code=stream.status_code,
        headers={**stream.headers, **secure_file_headers()},
        media_type=stream.media_type,
    )


@router.delete("/files/{file_id}")
async def delete_hardware_file(
    file_id: int,
    use_cases: inventory_hardware_use_cases_dep,
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    await dispatch_result_events(
        await use_cases.delete_file(
            file_id=file_id,
            audit=audit,
        ),
        events,
    )

    return {"status": "success"}

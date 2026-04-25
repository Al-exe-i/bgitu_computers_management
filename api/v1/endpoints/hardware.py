import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger

from core.exceptions import HTTP403, HTTP404
from db.session import session_dep
from dependencies.audit_actor import admin_audit_actor_dep, user_audit_actor_dep
from dependencies.auth import user_dep
from dependencies.hardware import hardware_service_dep
from dependencies.realtime import realtime_dep
from models.user import UserRole
from schemas.hardware import HardwareFullResponse, HardwareUpdate
from schemas.hardware_file import HardwareFileResponse
from utils.audit import clean_sensitive
from utils.broadcast import broadcast_audience_updated
from utils.telegram_notifications import enqueue_hardware_state_notification

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
    hardware_id: int,
    files: list[UploadFile],
    service: hardware_service_dep,
    db: session_dep,
    background_tasks: BackgroundTasks,
    audit: admin_audit_actor_dep,
    realtime: realtime_dep,
):
    hardware = await service.get(hardware_id)
    if not hardware:
        raise HTTP404("Hardware doesn't exist")

    result: list[HardwareFileResponse] = await service.update_files(hardware_id, files, db)
    logger.info(
        "Hardware files processed: hardware_id={} audience_id={} requested={} saved={}",
        hardware_id,
        hardware.audience_id,
        len(files),
        len(result),
    )

    await audit.log(
        action="hardware.file_add",
        entity_type="hardware",
        entity_id=hardware_id,
        payload={
            "audience_id": hardware.audience_id,
            "files_count": len(files),
            "filenames": [file.filename for file in files][:10],
        },
    )

    broadcast_audience_updated(background_tasks, realtime, hardware.audience_id)
    return {"status": "success", "files": result}


@router.patch("/{hardware_id}", response_model=HardwareFullResponse)
async def update_hardware(
    hardware_id: int,
    data: HardwareUpdate,
    service: hardware_service_dep,
    background_tasks: BackgroundTasks,
    audit: user_audit_actor_dep,
    realtime: realtime_dep,
):
    current_hw = await service.get(hardware_id)
    if not current_hw:
        raise HTTP404("Hardware not found")

    if data.state and audit.user.role == UserRole.teacher:
        logger.warning(
            "Hardware update rejected: teacher tried to mark good state user_id={} hardware_id={}",
            audit.user.id,
            hardware_id,
        )
        raise HTTP403("Teacher can't mark hardware as good state")

    if audit.user.role == UserRole.teacher:
        data = HardwareUpdate(**data.model_dump(include={"state"}))

    previous_state = current_hw.state
    updated_hw = await service.update(hardware_id, data)

    await audit.log(
        action="hardware.update",
        entity_type="hardware",
        entity_id=hardware_id,
        payload={
            "audience_id": updated_hw.audience_id,
            **(clean_sensitive(data) or {}),
        },
    )

    broadcast_audience_updated(background_tasks, realtime, updated_hw.audience_id)
    enqueue_hardware_state_notification(
        background_tasks,
        previous_state=previous_state,
        hardware=updated_hw,
        actor_user_id=audit.user.id,
    )
    return updated_hw


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    service: hardware_service_dep,
    user: user_dep,
):
    db_file = await service.get_file_for_stream(file_id)

    filename = os.path.basename(db_file.file_path)

    return FileResponse(
        path=db_file.file_path,
        media_type=db_file.file_type,
        filename=filename,
    )


@router.get("/stream/{file_id}")
async def stream_video(
    file_id: int,
    request: Request,
    service: hardware_service_dep,
    user: user_dep,
):
    db_file = await service.get_file_for_stream(file_id)
    file_path = db_file.file_path

    if not os.path.exists(file_path):
        logger.warning("Video stream file not found on disk: file_id={} path={}", file_id, file_path)
        raise HTTPException(status_code=404, detail="File not found")

    content_type = db_file.file_type
    if not content_type.startswith("video/"):
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith("video/"):
            content_type = mime_type
        else:
            logger.warning(
                "Video stream rejected: file_id={} content_type={} path={}",
                file_id,
                db_file.file_type,
                file_path,
            )
            raise HTTPException(status_code=415, detail="Not a video file")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")

    chunk_size = 1024 * 1024

    start = 0
    end = file_size - 1

    if range_header:
        try:
            range_str = range_header.replace("bytes=", "")
            range_parts = range_str.split("-")

            start = int(range_parts[0]) if range_parts[0] else 0

            if range_parts[1]:
                end = int(range_parts[1])
            else:
                end = min(start + chunk_size - 1, file_size - 1)

        except ValueError:
            logger.warning(
                "Video stream rejected: bad range header file_id={} range={}",
                file_id,
                range_header,
            )
            raise HTTPException(status_code=400, detail="Bad Range header")

    if start >= file_size:
        logger.warning(
            "Video stream rejected: unsatisfied range file_id={} start={} file_size={}",
            file_id,
            start,
            file_size,
        )
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    end = min(end, file_size - 1)

    content_length = end - start + 1

    def iter_file():
        with open(file_path, "rb") as file:
            file.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk_size_read = min(64 * 1024, remaining)
                data = file.read(chunk_size_read)
                if not data:
                    break
                yield data
                remaining -= len(data)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": content_type,
    }

    return StreamingResponse(
        iter_file(),
        status_code=206,
        headers=headers,
        media_type=content_type,
    )


@router.delete("/files/{file_id}")
async def delete_hardware_file(
    file_id: int,
    service: hardware_service_dep,
    background_tasks: BackgroundTasks,
    audit: admin_audit_actor_dep,
    realtime: realtime_dep,
):
    audience_id = await service.delete_file(file_id)
    logger.info("Hardware file deleted: file_id={} audience_id={}", file_id, audience_id)

    await audit.log(
        action="hardware.file_delete",
        entity_type="hardware_file",
        entity_id=file_id,
        payload={"audience_id": audience_id},
    )

    broadcast_audience_updated(background_tasks, realtime, audience_id)
    return {"status": "success"}

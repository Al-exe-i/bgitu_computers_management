from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi import Request
from core.exceptions import HTTP404, HTTP403
from db.session import session_dep
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep, user_dep
from dependencies.hardware import hardware_service_dep
from dependencies.request_meta import request_meta_dep
from models.user import UserRole
from schemas.hardware import HardwareFullResponse, HardwareUpdate
from fastapi.responses import FileResponse
import os
from schemas.hardware_file import HardwareFileResponse
from utils.audit import clean_sensitive
from utils.broadcast import broadcast_audience_updated

router = APIRouter()


@router.post("/{hardware_id}/files")
async def add_hardware_file(
        hardware_id: int,
        files: list[UploadFile],
        service: hardware_service_dep,
        db: session_dep,
        background_tasks: BackgroundTasks,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
):
    hardware = await service.get(hardware_id)
    if not hardware:
        raise HTTP404("Hardware doesn't exist")

    result: list[HardwareFileResponse] = await service.update_files(hardware_id, files, db)

    await audit.log(
        user_id=user.id,
        action="hardware.file_add",
        entity_type="hardware",
        entity_id=hardware_id,
        payload={
            "audience_id": hardware.audience_id,
            "files_count": len(files),
            "filenames": [f.filename for f in files][:10],  # чтобы лог не раздувался
        },
        **meta,
    )

    broadcast_audience_updated(background_tasks, hardware.audience_id)
    return {"status": "success", "files": result}


@router.patch("/{hardware_id}", response_model=HardwareFullResponse)
async def update_hardware_status(
        hardware_id: int,
        data: HardwareUpdate,
        service: hardware_service_dep,
        background_tasks: BackgroundTasks,
        user: user_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
):
    """
    Обновить статус, комментарий или позицию конкретного оборудования.
    """
    if data.state and user.role == UserRole.teacher:
        raise HTTP403("Teacher can't mark hardware as good state")

    if user.role == UserRole.teacher:
        data = HardwareUpdate(**data.model_dump(include={"state"}))

    updated_hw = await service.update_status(hardware_id, data)

    await audit.log(
        user_id=user.id,
        action="hardware.update",
        entity_type="hardware",
        entity_id=hardware_id,
        payload={
            "audience_id": updated_hw.audience_id,
            **(clean_sensitive(data) or {}),
        },
        **meta,
    )

    broadcast_audience_updated(background_tasks, updated_hw.audience_id)
    return updated_hw


@router.get("/files/{file_id}")
async def get_file(
        file_id: int,
        service: hardware_service_dep,
        user: user_dep
):
    db_file = await service.get_file_for_stream(file_id)

    filename = os.path.basename(db_file.file_path)

    return FileResponse(
        path=db_file.file_path,
        media_type=db_file.file_type,
        filename=filename
    )


@router.get("/stream/{file_id}")
async def stream_video(
        file_id: int,
        request: Request,
        service: hardware_service_dep,
        user: user_dep
):
    db_file = await service.get_file_for_stream(file_id)
    file_path = db_file.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    content_type = db_file.file_type
    if not content_type.startswith('video/'):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('video/'):
            content_type = mime_type
        else:
            raise HTTPException(status_code=415, detail="Not a video file")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")

    CHUNK_SIZE = 1024 * 1024

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
                end = min(start + CHUNK_SIZE - 1, file_size - 1)

        except ValueError:
            raise HTTPException(status_code=400, detail="Bad Range header")

    if start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    end = min(end, file_size - 1)

    content_length = end - start + 1

    def iter_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk_size_read = min(64 * 1024, remaining)
                data = f.read(chunk_size_read)
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
        media_type=content_type
    )


@router.delete("/files/{file_id}")
async def delete_hardware_file(
        file_id: int,
        service: hardware_service_dep,
        background_tasks: BackgroundTasks,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
):
    audience_id = await service.delete_file(file_id)

    await audit.log(
        user_id=user.id,
        action="hardware.file_delete",
        entity_type="hardware_file",
        entity_id=file_id,
        payload={"audience_id": audience_id},
        **meta,
    )

    broadcast_audience_updated(background_tasks, audience_id)
    return {"status": "success"}
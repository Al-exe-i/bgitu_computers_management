import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

from core.config import settings
from core.exceptions import HTTP403, HTTP404
from dependencies.auth import admin_dep

router = APIRouter(prefix="")


@router.get("/files/{file_path:path}")
async def get_protected_file(
        file_path: str,
        user: admin_dep
):
    full_path = os.path.join(settings.static.root, file_path)

    # Безопасность: проверяем, что файл действительно находится ВНУТРИ разрешенной папки
    abs_protected_dir = os.path.abspath(settings.static.root)
    abs_requested_path = os.path.abspath(full_path)

    if not abs_requested_path.startswith(abs_protected_dir):
        raise HTTP403("Доступ запрещен")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTP404("Файл не найден")

    return FileResponse(full_path)

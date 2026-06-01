from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends

from core.config import settings
from services.object_storage import LocalObjectStorage, MinioObjectStorage, ObjectStorage


@lru_cache
def get_object_storage() -> ObjectStorage:
    if settings.storage.backend == "minio":
        return MinioObjectStorage(
            endpoint=settings.storage.endpoint,
            access_key=settings.storage.access_key,
            secret_key=settings.storage.secret_key,
            bucket_name=settings.storage.bucket,
            secure=settings.storage.secure,
        )

    return LocalObjectStorage(settings.static.root)


object_storage_dep = Annotated[Any, Depends(get_object_storage)]

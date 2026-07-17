from pathlib import PurePosixPath


IMAGE_EXTENSIONS_BY_MEDIA_TYPE = {
    "image/avif": ".avif",
    "image/bmp": ".bmp",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

VIDEO_EXTENSIONS_BY_MEDIA_TYPE = {
    "video/mp4": ".mp4",
    "video/ogg": ".ogv",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-msvideo": ".avi",
}

HARDWARE_EXTENSIONS_BY_MEDIA_TYPE = {
    **IMAGE_EXTENSIONS_BY_MEDIA_TYPE,
    **VIDEO_EXTENSIONS_BY_MEDIA_TYPE,
}

SAFE_DOWNLOAD_MEDIA_TYPES = {
    **HARDWARE_EXTENSIONS_BY_MEDIA_TYPE,
    "application/pdf": ".pdf",
}

_MEDIA_TYPE_ALIASES = {"image/jpg": "image/jpeg"}
_IMAGE_MEDIA_TYPE_BY_EXTENSION = {
    extension: media_type
    for media_type, extension in IMAGE_EXTENSIONS_BY_MEDIA_TYPE.items()
}
_VIDEO_MEDIA_TYPE_BY_EXTENSION = {
    extension: media_type
    for media_type, extension in VIDEO_EXTENSIONS_BY_MEDIA_TYPE.items()
}


def normalize_media_type(value: str | None) -> str:
    normalized = (value or "").split(";", maxsplit=1)[0].strip().lower()
    return _MEDIA_TYPE_ALIASES.get(normalized, normalized)


def safe_image_media_type_for_filename(filename: str) -> str | None:
    extension = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    return _IMAGE_MEDIA_TYPE_BY_EXTENSION.get(extension)


def safe_video_media_type_for_filename(filename: str) -> str | None:
    extension = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    return _VIDEO_MEDIA_TYPE_BY_EXTENSION.get(extension)

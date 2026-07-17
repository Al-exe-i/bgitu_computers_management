import re
from pathlib import PurePosixPath
from urllib.parse import quote


def secure_file_headers(
    filename: str | None = None,
    *,
    as_attachment: bool = False,
) -> dict[str, str]:
    headers = {
        "Cache-Control": "private, no-cache",
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-Content-Type-Options": "nosniff",
    }

    if filename:
        basename = PurePosixPath(filename.replace("\\", "/")).name
        fallback = re.sub(r"[^A-Za-z0-9._-]", "_", basename) or "file"
        encoded = quote(basename, safe="")
        disposition = "attachment" if as_attachment else "inline"
        headers["Content-Disposition"] = (
            f'{disposition}; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'
        )

    return headers

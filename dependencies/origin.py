from urllib.parse import urlsplit

from fastapi import Request

from core.config import settings
from core.exceptions import HTTP403


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _normalized_origin(value: str | None) -> str | None:
    if not value:
        return None

    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None

    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def enforce_trusted_origin(request: Request) -> None:
    if request.method.upper() in SAFE_METHODS:
        return

    supplied_origin = request.headers.get("origin")
    candidate = _normalized_origin(supplied_origin)

    if supplied_origin is None:
        referer = request.headers.get("referer")
        if referer is None:
            # Bearer/CLI clients do not need CSRF protection, unlike cookie-authenticated requests.
            if request.cookies.get("access_token") or request.cookies.get("refresh_token"):
                raise HTTP403("Missing request origin")
            return
        candidate = _normalized_origin(referer)

    trusted_origins = {
        origin
        for value in [settings.frontend_url, *settings.cors_origins]
        if (origin := _normalized_origin(value)) is not None
    }
    if candidate is None or candidate not in trusted_origins:
        raise HTTP403("Untrusted request origin")

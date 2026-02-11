# utils/request_meta.py
from typing import TypedDict
from fastapi import Request


class RequestMeta(TypedDict):
    ip: str | None
    user_agent: str | None
    path: str | None
    method: str | None


def _get_client_ip(request: Request) -> str | None:
    """
    Достаём IP аккуратно.
    Важно: X-Forwarded-For можно доверять только если ты реально за прокси
    и настроил forwarded headers (иначе можно подделать).
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Берём первый IP из списка "client, proxy1, proxy2"
        ip = xff.split(",")[0].strip()
        return ip or None

    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip() or None

    if request.client:
        return request.client.host

    return None


def get_request_meta(request: Request) -> RequestMeta:
    return {
        "ip": _get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "method": request.method,
    }
from ipaddress import ip_address, ip_network
from typing import TypedDict

from fastapi import Request

from core.config import settings


class RequestMeta(TypedDict):
    ip: str | None
    user_agent: str | None
    path: str | None
    method: str | None


def _parse_ip(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    try:
        return str(ip_address(candidate))
    except ValueError:
        return None


def _is_trusted_proxy(client_host: str | None) -> bool:
    client_ip = _parse_ip(client_host)
    if client_ip is None:
        return False

    parsed_client_ip = ip_address(client_ip)
    for trusted in settings.trusted_proxy_ips:
        try:
            trusted_network = ip_network(trusted, strict=False)
        except ValueError:
            continue

        if parsed_client_ip in trusted_network:
            return True

    return False


def _get_forwarded_ip(request: Request) -> str | None:
    client_host = request.client.host if request.client else None
    if not _is_trusted_proxy(client_host):
        return None

    xff = request.headers.get("x-forwarded-for")
    if xff:
        first_ip = xff.split(",", maxsplit=1)[0]
        parsed_ip = _parse_ip(first_ip)
        if parsed_ip:
            return parsed_ip

    return _parse_ip(request.headers.get("x-real-ip"))


def _get_client_ip(request: Request) -> str | None:
    forwarded_ip = _get_forwarded_ip(request)
    if forwarded_ip:
        return forwarded_ip

    if request.client:
        return _parse_ip(request.client.host) or request.client.host

    return None


def get_request_meta(request: Request) -> RequestMeta:
    return {
        "ip": _get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "method": request.method,
    }

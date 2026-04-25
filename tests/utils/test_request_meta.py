from fastapi import Request

from core.config import settings
from utils.request_meta import get_request_meta


def make_request(
    *,
    path: str = "/api/v1/test",
    method: str = "GET",
    headers: list[tuple[bytes, bytes]] | None = None,
    client: tuple[str, int] | None = ("127.0.0.1", 12345),
) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "scheme": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers or [],
        "client": client,
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_get_request_meta_ignores_forwarded_headers_from_untrusted_client(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_ips", [])
    request = make_request(
        headers=[
            (b"x-forwarded-for", b"203.0.113.10, 10.0.0.2"),
            (b"x-real-ip", b"198.51.100.5"),
            (b"user-agent", b"pytest"),
        ],
        client=("192.0.2.33", 12345),
    )

    meta = get_request_meta(request)

    assert meta == {
        "ip": "192.0.2.33",
        "user_agent": "pytest",
        "path": "/api/v1/test",
        "method": "GET",
    }


def test_get_request_meta_trusts_x_forwarded_for_from_trusted_proxy(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_ips", ["10.0.0.0/8"])
    request = make_request(
        headers=[
            (b"x-forwarded-for", b"203.0.113.10, 10.0.0.2"),
            (b"user-agent", b"pytest"),
        ],
        client=("10.0.0.2", 12345),
    )

    assert get_request_meta(request)["ip"] == "203.0.113.10"


def test_get_request_meta_falls_back_to_x_real_ip_for_trusted_proxy(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_ips", ["10.0.0.2"])
    proxy_request = make_request(
        headers=[(b"x-real-ip", b"198.51.100.5")],
        client=("10.0.0.2", 12345),
    )

    assert get_request_meta(proxy_request)["ip"] == "198.51.100.5"


def test_get_request_meta_falls_back_to_client_host(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_ips", [])
    direct_request = make_request(headers=[], client=("192.0.2.33", 4444))

    assert get_request_meta(direct_request)["ip"] == "192.0.2.33"

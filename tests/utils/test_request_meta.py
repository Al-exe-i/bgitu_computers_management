from fastapi import Request

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


def test_get_request_meta_prefers_x_forwarded_for() -> None:
    request = make_request(
        headers=[
            (b"x-forwarded-for", b"203.0.113.10, 10.0.0.2"),
            (b"user-agent", b"pytest"),
        ]
    )

    meta = get_request_meta(request)

    assert meta == {
        "ip": "203.0.113.10",
        "user_agent": "pytest",
        "path": "/api/v1/test",
        "method": "GET",
    }


def test_get_request_meta_falls_back_to_x_real_ip_and_client_host() -> None:
    proxy_request = make_request(headers=[(b"x-real-ip", b"198.51.100.5")])
    direct_request = make_request(headers=[], client=("192.0.2.33", 4444))

    assert get_request_meta(proxy_request)["ip"] == "198.51.100.5"
    assert get_request_meta(direct_request)["ip"] == "192.0.2.33"

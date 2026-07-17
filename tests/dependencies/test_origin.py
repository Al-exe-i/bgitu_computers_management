import pytest

from core.config import settings
from core.exceptions import HTTP403
from dependencies.origin import enforce_trusted_origin
from tests.utils.test_request_meta import make_request


def test_trusted_origin_allows_configured_frontend(monkeypatch) -> None:
    monkeypatch.setattr(settings, "frontend_url", "https://app.example.ru")
    request = make_request(
        method="POST",
        headers=[(b"origin", b"https://app.example.ru")],
    )

    enforce_trusted_origin(request)


def test_trusted_origin_rejects_cross_site_browser_request(monkeypatch) -> None:
    monkeypatch.setattr(settings, "frontend_url", "https://app.example.ru")
    monkeypatch.setattr(settings, "cors_origins", ["https://app.example.ru"])
    request = make_request(
        method="POST",
        headers=[(b"origin", b"https://attacker.example")],
    )

    with pytest.raises(HTTP403, match="Untrusted request origin"):
        enforce_trusted_origin(request)


def test_trusted_origin_allows_non_browser_client_without_origin_headers() -> None:
    enforce_trusted_origin(make_request(method="POST"))


def test_cookie_authenticated_request_without_origin_is_rejected() -> None:
    request = make_request(
        method="POST",
        headers=[(b"cookie", b"access_token=token")],
    )

    with pytest.raises(HTTP403, match="Missing request origin"):
        enforce_trusted_origin(request)

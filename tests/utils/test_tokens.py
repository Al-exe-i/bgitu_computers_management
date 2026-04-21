import hashlib
from uuid import UUID

from core.config import settings
from core.security import verify_access_token
from utils.tokens import (
    build_token_response,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
)


def test_issue_access_token_creates_valid_jwt_for_user() -> None:
    token = issue_access_token(42)

    payload = verify_access_token(token)

    assert payload is not None
    assert payload["sub"] == "42"


def test_new_refresh_token_returns_unique_uuid_strings() -> None:
    first_token = new_refresh_token()
    second_token = new_refresh_token()

    assert UUID(first_token)
    assert UUID(second_token)
    assert first_token != second_token


def test_hash_refresh_token_returns_sha256_hex_digest() -> None:
    token = "refresh-token"

    assert hash_refresh_token(token) == hashlib.sha256(token.encode("utf-8")).hexdigest()


def test_build_token_response_sets_body_and_cookies() -> None:
    response = build_token_response(access_token="access", refresh_token="refresh")
    cookies = response.headers.getlist("set-cookie")

    assert (
        response.body
        == b'{"access_token":"access","token_type":"bearer","status":"success"}'
    )
    assert len(cookies) == 2
    assert "access_token=access" in cookies[0]
    assert (
        f"Max-Age={settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES * 60}"
        in cookies[0]
    )
    assert "refresh_token=refresh" in cookies[1]
    assert (
        f"Max-Age={settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60}"
        in cookies[1]
    )

    for cookie in cookies:
        assert "HttpOnly" in cookie
        assert "Path=/" in cookie
        assert "SameSite=lax" in cookie
        assert ("Secure" in cookie) is (not settings.DEBUG)

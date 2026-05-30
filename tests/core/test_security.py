from core.security import (
    generate_access_token,
    get_password_hash,
    verify_access_token,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    password = "strong-password"
    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_access_token_roundtrip_preserves_payload() -> None:
    token = generate_access_token({"sub": "17", "role": "admin"})

    payload = verify_access_token(token)

    assert payload is not None
    assert payload["sub"] == "17"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload
    assert "nbf" in payload


def test_verify_access_token_returns_none_for_invalid_token() -> None:
    assert (
        verify_access_token(
            "not-a-jwt-some-trash-here-to-suppress-length-error-777-999-888"
        )
        is None
    )

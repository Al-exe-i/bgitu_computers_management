from pydantic import BaseModel

from utils.audit import changed_fields, clean_sensitive


class AuditPayload(BaseModel):
    name: str
    password: str
    nested: dict


def test_clean_sensitive_masks_nested_sensitive_fields() -> None:
    payload = {
        "email": "user@example.com",
        "password": "secret",
        "profile": {
            "token": "abc",
            "api_key": "key",
            "safe": "value",
        },
        "items": [
            {"refresh_token": "refresh"},
            {"name": "visible"},
        ],
    }

    cleaned = clean_sensitive(payload)

    assert cleaned == {
        "email": "user@example.com",
        "password": "***",
        "profile": {
            "token": "***",
            "api_key": "***",
            "safe": "value",
        },
        "items": [
            {"refresh_token": "***"},
            {"name": "visible"},
        ],
    }


def test_clean_sensitive_supports_pydantic_models() -> None:
    payload = AuditPayload(
        name="Alex",
        password="top-secret",
        nested={"access_token": "jwt", "comment": "keep"},
    )

    cleaned = clean_sensitive(payload)

    assert cleaned["name"] == "Alex"
    assert cleaned["password"] == "***"
    assert cleaned["nested"] == {"access_token": "***", "comment": "keep"}


def test_changed_fields_returns_sorted_keys_and_respects_exclude() -> None:
    payload = {"surname": "Ivanov", "name": "Alex", "password": "secret"}

    assert changed_fields(payload) == ["name", "password", "surname"]
    assert changed_fields(payload, exclude={"password"}) == ["name", "surname"]

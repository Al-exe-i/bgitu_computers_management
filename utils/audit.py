from collections.abc import Iterable

from pydantic import BaseModel

SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "api_key"}


def clean_sensitive(obj):
    if obj is None:
        return None
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(exclude_unset=True)
    if isinstance(obj, dict):
        clean = {}
        for key, value in obj.items():
            if key.lower() in SENSITIVE_KEYS:
                clean[key] = "***"
            else:
                clean[key] = clean_sensitive(value)
        return clean
    if isinstance(obj, list):
        return [clean_sensitive(item) for item in obj]
    return obj


def changed_fields(obj, *, exclude: Iterable[str] | None = None) -> list[str]:
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(exclude_unset=True)

    if not isinstance(obj, dict):
        return []

    excluded = set(exclude or ())
    return sorted(key for key in obj.keys() if key not in excluded)

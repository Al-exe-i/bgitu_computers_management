from pydantic import TypeAdapter, ValidationError

from core.exceptions.management import ManagementUserError
from utils.email import RU_EMAIL_ERROR, RuEmailStr

_EMAIL_ADAPTER = TypeAdapter(RuEmailStr)


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not value:
        raise ManagementUserError("Email/login must not be empty")
    return value


def validate_new_user_email(email: str) -> str:
    value = normalize_email(email)
    try:
        validated = str(_EMAIL_ADAPTER.validate_python(value))
    except (ValidationError, ValueError) as exc:
        raise ManagementUserError(RU_EMAIL_ERROR) from exc
    if len(validated) > 50:
        raise ManagementUserError("Email must contain at most 50 characters")
    return validated


def validate_password(password: str) -> str:
    if len(password) < 6:
        raise ManagementUserError("Password must contain at least 6 characters")
    if len(password) > 128:
        raise ManagementUserError("Password must contain at most 128 characters")
    return password

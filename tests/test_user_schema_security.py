import pytest
from pydantic import ValidationError

from modules.identity.schemas.user import ResetUserPasswordSchema, UserUpdate


@pytest.mark.parametrize("password", ["", "short", "x" * 129])
def test_reset_password_rejects_invalid_length(password):
    with pytest.raises(ValidationError):
        ResetUserPasswordSchema(new_password=password)


def test_reset_password_rejects_extra_fields_and_hides_repr():
    with pytest.raises(ValidationError):
        ResetUserPasswordSchema(new_password="secret12", is_superuser=True)
    assert "secret12" not in repr(ResetUserPasswordSchema(new_password="secret12"))


@pytest.mark.parametrize(
    "forbidden_field",
    [
        {"password": "new-password"},
        {"photo": "attacker-controlled.html"},
    ],
)
def test_public_user_update_rejects_protected_fields(forbidden_field) -> None:
    with pytest.raises(ValidationError):
        UserUpdate.model_validate(forbidden_field)

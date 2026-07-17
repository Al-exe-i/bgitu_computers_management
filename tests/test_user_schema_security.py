import pytest
from pydantic import ValidationError

from schemas.user import UserUpdate


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

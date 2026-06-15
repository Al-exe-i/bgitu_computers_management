import pytest
from pydantic import BaseModel, ValidationError

from utils.email import RuEmailStr


class EmailPayload(BaseModel):
    email: RuEmailStr


def test_ru_email_accepts_ru_domain() -> None:
    payload = EmailPayload(email="USER@EXAMPLE.RU")

    assert str(payload.email).lower() == "user@example.ru"


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user@example.ru.com",
        "not-an-email",
    ],
)
def test_ru_email_rejects_non_ru_or_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        EmailPayload(email=email)

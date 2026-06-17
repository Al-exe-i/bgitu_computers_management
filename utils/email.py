from typing import Annotated

from pydantic import AfterValidator, EmailStr


RU_EMAIL_ERROR = "Email must use a .ru domain"


def validate_ru_email_domain(email: str) -> str:
    # Приводим логин целиком к нижнему регистру, чтобы в БД он хранился нормализованным
    value = str(email).strip().lower()
    domain = value.rsplit("@", 1)[-1]

    if not domain.endswith(".ru"):
        raise ValueError(RU_EMAIL_ERROR)

    return value


RuEmailStr = Annotated[EmailStr, AfterValidator(validate_ru_email_domain)]

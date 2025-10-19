from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Set

from models import Office, Audience

OFFICE_AUDIENCE_RULES: dict[int, Set[int]] = {
    1: {157, 158, 150, 161, 152, 153, 154, 155, 203, 206, 209, 204, 207, 211, 224, 223, 214, 215, 227, 216, 218, 217,
        219, 220, 226, 228, 229, 233, 234, 235},
    2: {257, 481, 482}
}


def validate_audience_on_save(mapper, connection, target):
    """Проверяет ID аудитории относительно ее связанного корпуса перед INSERT/UPDATE."""

    audience_id = target.id
    office_id = target.office_id

    if audience_id is not None and office_id in OFFICE_AUDIENCE_RULES:

        acceptable_ids = OFFICE_AUDIENCE_RULES[office_id]

        if audience_id not in acceptable_ids:
            error_msg = (
                f"Ошибка целостности: Аудитория с ID {audience_id} не разрешена для "
                f"корпуса с ID {office_id}."
            )
            raise IntegrityError(error_msg, params=None, orig=None)


def setup_listeners():
    """Функция для установки всех слушателей"""
    event.listen(Audience, "before_insert", validate_audience_on_save)
    event.listen(Audience, "before_update", validate_audience_on_save)
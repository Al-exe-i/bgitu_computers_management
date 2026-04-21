from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.exceptions import HTTP403
from models.user import UserRole
from schemas.user import UserOut
from utils.permissions import can_change_other_su


def make_target_user(*, user_id: int, is_superuser: bool) -> UserOut:
    return UserOut(
        id=user_id,
        email="user@example.com",
        name="Alex",
        surname="Ivanov",
        telegram_id=None,
        telegram_id_confirmed=False,
        photo=None,
        role=UserRole.admin,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=is_superuser,
    )


def test_can_change_other_su_allows_editing_self() -> None:
    current_user = SimpleNamespace(id=7)
    target_user = make_target_user(user_id=7, is_superuser=True)

    can_change_other_su(current_user, target_user)


def test_can_change_other_su_allows_non_superuser_targets() -> None:
    current_user = SimpleNamespace(id=1)
    target_user = make_target_user(user_id=2, is_superuser=False)

    can_change_other_su(current_user, target_user)


def test_can_change_other_su_rejects_editing_another_superuser() -> None:
    current_user = SimpleNamespace(id=1)
    target_user = make_target_user(user_id=2, is_superuser=True)

    with pytest.raises(HTTP403, match="another superuser"):
        can_change_other_su(current_user, target_user)

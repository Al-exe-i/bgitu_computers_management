import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.exceptions import HTTP401, HTTP403
from core.security import generate_access_token
from dependencies.auth import (
    _validate_token_and_get_user,
    get_admin,
    get_current_superuser,
    get_current_user,
)
from models.user import UserRole
from schemas.user import UserOut
from utils.tokens import issue_access_token


class DummyUserService:
    def __init__(self, users: dict[int, object]) -> None:
        self.users = users

    async def get(self, user_id: int):
        return self.users.get(user_id)


def make_user(*, user_id: int, role: UserRole = UserRole.admin, is_superuser: bool = False) -> UserOut:
    return UserOut(
        id=user_id,
        email=f"user{user_id}@example.com",
        name="Alex",
        surname="Ivanov",
        photo=None,
        role=role,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=is_superuser,
    )


def test_get_current_user_prefers_cookie_token_over_header_token() -> None:
    async def scenario() -> None:
        cookie_user = make_user(user_id=7)
        header_user = make_user(user_id=8)
        service = DummyUserService({7: cookie_user, 8: header_user})

        user = await get_current_user(
            service,
            access_token_cookie=issue_access_token(7),
            access_token_header=issue_access_token(8),
        )

        assert user.id == 7

    asyncio.run(scenario())


def test_get_current_user_accepts_bearer_token_from_header_when_cookie_missing() -> None:
    async def scenario() -> None:
        expected_user = make_user(user_id=11)
        service = DummyUserService({11: expected_user})

        user = await get_current_user(
            service,
            access_token_cookie=None,
            access_token_header=issue_access_token(11),
        )

        assert user == expected_user

    asyncio.run(scenario())


def test_get_current_user_rejects_missing_token() -> None:
    async def scenario() -> None:
        with pytest.raises(HTTP401, match="Not authenticated"):
            await get_current_user(
                DummyUserService({}),
                access_token_cookie=None,
                access_token_header=None,
            )

    asyncio.run(scenario())


def test_get_current_superuser_rejects_non_superuser() -> None:
    async def scenario() -> None:
        with pytest.raises(HTTP403, match="Not enough permissions"):
            await get_current_superuser(make_user(user_id=1, is_superuser=False))

    asyncio.run(scenario())


def test_get_admin_rejects_teacher_role() -> None:
    async def scenario() -> None:
        with pytest.raises(HTTP403, match="Not enough permissions"):
            await get_admin(make_user(user_id=1, role=UserRole.teacher))

    asyncio.run(scenario())


def test_validate_token_accepts_matching_access_token_version() -> None:
    async def scenario() -> None:
        user = SimpleNamespace(id=7, access_token_version=2)
        token = issue_access_token(7, token_version=2)

        result = await _validate_token_and_get_user(token, DummyUserService({7: user}))

        assert result is user

    asyncio.run(scenario())


def test_validate_token_rejects_stale_access_token_version() -> None:
    async def scenario() -> None:
        user = SimpleNamespace(id=7, access_token_version=2)
        token = issue_access_token(7, token_version=1)

        with pytest.raises(HTTP401, match="Couldn't validate credentials"):
            await _validate_token_and_get_user(token, DummyUserService({7: user}))

    asyncio.run(scenario())


def test_validate_token_treats_legacy_token_without_version_as_zero() -> None:
    async def scenario() -> None:
        user = SimpleNamespace(id=7, access_token_version=0)
        token = generate_access_token({"sub": "7"})

        result = await _validate_token_and_get_user(token, DummyUserService({7: user}))

        assert result is user

    asyncio.run(scenario())

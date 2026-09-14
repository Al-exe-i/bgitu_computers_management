import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.security import verify_password
from modules.identity.contracts import UserCredentials
from modules.identity.public import AuthenticatedUser, UserOut, UserRole
from modules.identity.services.users import UserService


@pytest.fixture
def user():
    return SimpleNamespace(
        id=7, name="Alex", surname=None, email="user@example.ru", photo=None,
        reg_date=datetime(2026, 9, 7, tzinfo=UTC), is_superuser=False,
        role=UserRole.teacher, access_token_version=3, password="private-hash",
    )


def test_read_boundaries_return_detached_safe_data(user):
    async def scenario():
        repo = SimpleNamespace(
            get=AsyncMock(return_value=user), get_all=AsyncMock(return_value=[user]),
            get_by_email=AsyncMock(return_value=user),
        )
        service = UserService(repo)
        profile = await service.get(user.id)
        users = await service.get_all()
        principal = await service.get_for_authentication(user.id)
        credentials = await service.get_by_email(user.email)

        assert type(profile) is UserOut
        assert type(users[0]) is UserOut
        assert type(principal) is AuthenticatedUser
        assert principal.access_token_version == 3
        for dto in (profile, users[0], principal):
            assert "password" not in dto.model_dump()
            assert "access_token_version" not in dto.model_dump()
            assert not hasattr(dto, "_sa_instance_state")
        assert isinstance(credentials, UserCredentials)
        assert credentials.password == user.password
        assert "private-hash" not in repr(credentials)
        user.name = "Changed"
        assert profile.name == principal.name == "Alex"

    asyncio.run(scenario())


def test_password_is_hashed_before_it_reaches_repository(user):
    async def scenario():
        repo = SimpleNamespace(get=AsyncMock(return_value=user), update_password=AsyncMock(return_value=user))
        result = await UserService(repo).update_password(user.id, "new-password")
        stored_hash = repo.update_password.await_args.args[1]
        assert stored_hash != "new-password"
        assert verify_password("new-password", stored_hash)
        assert type(result) is UserOut

    asyncio.run(scenario())

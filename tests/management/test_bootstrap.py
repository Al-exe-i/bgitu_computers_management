import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import management.bootstrap as bootstrap_module
from core.config import BootstrapConfig, BootstrapOfficeConfig
from management.bootstrap import (
    BootstrapError,
    ensure_initial_superuser,
    ensure_offices,
)
from management.users import ManagedUserResult
from modules.identity.models.user import User
from modules.identity.public import UserRole


def test_existing_superuser_is_never_modified() -> None:
    async def scenario() -> None:
        existing = User(
            id=4,
            email="existing@example.ru",
            password="hash",
            role=UserRole.admin,
            is_superuser=True,
        )
        session = MagicMock()
        session.scalar = AsyncMock(return_value=existing)
        config = BootstrapConfig(
            offices=[],
            superuser_email="another@example.ru",
            superuser_password="another-password",
        )

        result, created = await ensure_initial_superuser(session, config)

        assert created is False
        assert result is not None
        assert result.id == 4
        assert result.email == "existing@example.ru"

    asyncio.run(scenario())


def test_empty_database_requires_initial_superuser_credentials() -> None:
    async def scenario() -> None:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)

        with pytest.raises(BootstrapError, match="No superuser exists"):
            await ensure_initial_superuser(
                session,
                BootstrapConfig(offices=[]),
            )

    asyncio.run(scenario())


def test_bootstrap_creates_initial_superuser_once(monkeypatch) -> None:
    async def scenario() -> None:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)

        async def get_user_by_email(_session, _email):
            return None

        async def create_admin_user(_session, **_kwargs):
            return ManagedUserResult(
                id=8,
                email="admin@example.ru",
                role=UserRole.admin,
                is_superuser=True,
            )

        monkeypatch.setattr(bootstrap_module, "get_user_by_email", get_user_by_email)
        monkeypatch.setattr(bootstrap_module, "create_admin_user", create_admin_user)

        result, created = await ensure_initial_superuser(
            session,
            BootstrapConfig(
                offices=[],
                superuser_email="admin@example.ru",
                superuser_password="strong-password",
            ),
        )

        assert created is True
        assert result is not None
        assert result.id == 8

    asyncio.run(scenario())


def test_bootstrap_offices_do_not_overwrite_existing_data() -> None:
    async def scenario() -> None:
        existing = MagicMock(address="Переименованный корпус")
        session = MagicMock()
        session.get = AsyncMock(return_value=existing)
        session.scalar = AsyncMock()
        session.flush = AsyncMock()

        created = await ensure_offices(
            session,
            [BootstrapOfficeConfig(id=1, address="Корпус №1")],
        )

        assert created == []
        session.add.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(scenario())

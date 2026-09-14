import argparse
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.security import verify_password
from management.users import (
    RU_EMAIL_ERROR,
    ManagementUserError,
    build_managed_user,
    build_parser,
    normalize_email,
    reset_user_password,
    resolve_password,
    validate_password,
)
from modules.identity.models.user import User
from modules.identity.public import UserRole


def test_build_parser_parses_create_superuser_command():
    args = build_parser().parse_args(
        [
            "create-su",
            "--email",
            "su",
            "--password",
            "secret123",
        ]
    )

    assert args.command == "create-su"
    assert args.email == "su"
    assert args.password == "secret123"


def test_build_managed_user_hashes_password_and_sets_admin_role():
    user = build_managed_user(
        email=" admin@example.ru ",
        password="secret123",
        role=UserRole.admin,
        is_superuser=True,
    )

    assert user.email == "admin@example.ru"
    assert user.role == UserRole.admin
    assert user.is_superuser is True
    assert user.password != "secret123"
    assert verify_password("secret123", user.password)


def test_password_can_be_resolved_from_env(monkeypatch):
    monkeypatch.setenv("BGITU_TEST_PASSWORD", "secret123")
    args = argparse.Namespace(password=None, password_env="BGITU_TEST_PASSWORD")

    assert resolve_password(args) == "secret123"


@pytest.mark.parametrize("password", ["", "short"])
def test_validate_password_rejects_short_password(password):
    with pytest.raises(ManagementUserError):
        validate_password(password)


def test_normalize_email_rejects_empty_value():
    with pytest.raises(ManagementUserError):
        normalize_email("   ")


def test_normalize_email_is_case_insensitive():
    assert normalize_email(" Admin@Example.RU ") == "admin@example.ru"


def test_build_managed_user_rejects_non_ru_email():
    with pytest.raises(ManagementUserError, match=RU_EMAIL_ERROR):
        build_managed_user(
            email="admin@example.com",
            password="secret123",
            role=UserRole.admin,
            is_superuser=True,
        )


def test_reset_password_revokes_sessions_and_invalidates_access_tokens():
    async def scenario() -> None:
        user = User(
            id=7,
            email="admin@example.ru",
            password="old-hash",
            role=UserRole.admin,
            is_superuser=True,
            access_token_version=3,
        )
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user

        session = MagicMock()
        session.execute = AsyncMock(side_effect=[user_result, MagicMock()])
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        result = await reset_user_password(
            session,
            email="ADMIN@example.ru",
            password="new-secret",
        )

        assert result.id == 7
        assert user.access_token_version == 4
        assert verify_password("new-secret", user.password)
        assert session.execute.await_count == 2

    asyncio.run(scenario())

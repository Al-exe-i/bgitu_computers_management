import argparse
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.exceptions.management import ManagementUserError
from core.security import verify_password
from management.users import build_parser, resolve_password
from modules.identity.management_validation import normalize_email, validate_password
from modules.identity.public import UserRole
from modules.identity.services.management import ManagedUserService
from utils.email import RU_EMAIL_ERROR


@pytest.fixture
def managed():
    async def create(user):
        user.id = 7
        return user

    users = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        create_managed=AsyncMock(side_effect=create),
        reset_managed_password=AsyncMock(
            return_value=SimpleNamespace(
                id=7,
                email="admin@example.ru",
                role=UserRole.admin,
                is_superuser=True,
            )
        ),
    )
    sessions = SimpleNamespace(revoke_all_for_user=AsyncMock())
    cache = SimpleNamespace(invalidate=AsyncMock())
    hooks = []
    return (
        ManagedUserService(users, sessions, cache, on_commit=hooks.append),
        users,
        sessions,
        cache,
        hooks,
    )


def test_build_parser_parses_create_superuser_command():
    args = build_parser().parse_args(
        ["create-su", "--email", "su", "--password", "secret123"]
    )
    assert (args.command, args.email, args.password) == ("create-su", "su", "secret123")


def test_password_can_be_resolved_from_env(monkeypatch):
    monkeypatch.setenv("BGITU_TEST_PASSWORD", "secret123")
    args = argparse.Namespace(password=None, password_env="BGITU_TEST_PASSWORD")
    assert resolve_password(args) == "secret123"


@pytest.mark.parametrize("password", ["", "short", "x" * 129])
def test_validate_password_rejects_invalid_length(password):
    with pytest.raises(ManagementUserError):
        validate_password(password)


def test_normalize_email_rejects_empty_value():
    with pytest.raises(ManagementUserError):
        normalize_email("   ")


def test_normalize_email_is_case_insensitive():
    assert normalize_email(" Admin@Example.RU ") == "admin@example.ru"


def test_create_hashes_password_and_sets_admin_role(managed):
    service, users, _, _, _ = managed
    result = asyncio.run(
        service.create_admin_user(
            email=" Admin@Example.RU ",
            password="secret123",
            is_superuser=True,
        )
    )
    user = users.create_managed.call_args.args[0]
    assert (result.email, result.role, result.is_superuser) == (
        "admin@example.ru",
        UserRole.admin,
        True,
    )
    assert verify_password("secret123", user.password)
    assert "secret123" not in repr(result)


def test_create_rejects_non_ru_email_before_db_write(managed):
    service, users, _, _, _ = managed
    with pytest.raises(ManagementUserError, match=RU_EMAIL_ERROR):
        asyncio.run(
            service.create_admin_user(
                email="admin@example.com", password="secret123", is_superuser=True
            )
        )
    users.create_managed.assert_not_awaited()


def test_create_rejects_existing_user(managed):
    service, users, _, _, _ = managed
    users.get_by_email.return_value = object()
    with pytest.raises(ManagementUserError, match="already exists"):
        asyncio.run(
            service.create_admin_user(
                email="admin@example.ru", password="secret123", is_superuser=False
            )
        )
    users.create_managed.assert_not_awaited()


def test_reset_password_revokes_sessions_and_schedules_cache_invalidation(managed):
    service, users, sessions, cache, hooks = managed
    result = asyncio.run(
        service.reset_user_password(email=" Admin@Example.RU ", password="new-secret")
    )
    email, hashed = users.reset_managed_password.call_args.args
    assert email == "admin@example.ru" and verify_password("new-secret", hashed)
    assert result.id == 7
    sessions.revoke_all_for_user.assert_awaited_once_with(7)
    cache.invalidate.assert_not_awaited()
    assert len(hooks) == 1
    asyncio.run(hooks[0]())
    cache.invalidate.assert_awaited_once_with(7)


def test_reset_missing_user_does_not_revoke_or_schedule(managed):
    service, users, sessions, _, hooks = managed
    users.reset_managed_password.return_value = None
    with pytest.raises(ManagementUserError, match="not found"):
        asyncio.run(
            service.reset_user_password(email="legacy-login", password="secret123")
        )
    sessions.revoke_all_for_user.assert_not_awaited()
    assert hooks == []

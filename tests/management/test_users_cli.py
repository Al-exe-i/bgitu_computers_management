import argparse

import pytest

from core.security import verify_password
from management.users import (
    ManagementUserError,
    build_managed_user,
    build_parser,
    normalize_email,
    resolve_password,
    validate_password,
)
from models.user import UserRole


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
        email=" admin ",
        password="secret123",
        role=UserRole.admin,
        is_superuser=True,
    )

    assert user.email == "admin"
    assert user.role == UserRole.admin
    assert user.is_superuser is True
    assert user.telegram_id_confirmed is False
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

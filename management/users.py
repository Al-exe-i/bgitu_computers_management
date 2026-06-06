from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from getpass import getpass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash
from db.session import engine, session_factory
from models.user import User, UserRole


class ManagementUserError(Exception):
    """Raised for expected management command errors."""


@dataclass(slots=True, frozen=True)
class ManagedUserResult:
    id: int
    email: str
    role: UserRole
    is_superuser: bool


def normalize_email(email: str) -> str:
    value = email.strip()
    if not value:
        raise ManagementUserError("Email/login must not be empty")
    return value


def validate_password(password: str) -> str:
    if len(password) < 6:
        raise ManagementUserError("Password must contain at least 6 characters")
    return password


def build_managed_user(
    *,
    email: str,
    password: str,
    role: UserRole,
    is_superuser: bool,
    name: str | None = None,
    surname: str | None = None,
) -> User:
    return User(
        email=normalize_email(email),
        password=get_password_hash(validate_password(password)),
        role=role,
        is_superuser=is_superuser,
        name=name,
        surname=surname,
    )


def to_result(user: User) -> ManagedUserResult:
    return ManagedUserResult(
        id=user.id,
        email=user.email,
        role=user.role,
        is_superuser=user.is_superuser,
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == normalize_email(email)))
    return result.scalar_one_or_none()


async def create_admin_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    is_superuser: bool,
    name: str | None = None,
    surname: str | None = None,
) -> ManagedUserResult:
    normalized_email = normalize_email(email)
    existing = await get_user_by_email(session, normalized_email)
    if existing is not None:
        raise ManagementUserError(f"User already exists: {normalized_email}")

    user = build_managed_user(
        email=normalized_email,
        password=password,
        role=UserRole.admin,
        is_superuser=is_superuser,
        name=name,
        surname=surname,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return to_result(user)


async def reset_user_password(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> ManagedUserResult:
    user = await get_user_by_email(session, email)
    if user is None:
        raise ManagementUserError(f"User not found: {normalize_email(email)}")

    user.password = get_password_hash(validate_password(password))
    await session.flush()
    await session.refresh(user)
    return to_result(user)


def add_password_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--password",
        help="Password value. Avoid this in shared shells because it can be stored in shell history.",
    )
    group.add_argument(
        "--password-env",
        help="Environment variable name containing password.",
    )


def resolve_password(args: argparse.Namespace) -> str:
    if args.password_env:
        password = os.getenv(args.password_env)
        if password is None:
            raise ManagementUserError(f"Environment variable is not set: {args.password_env}")
        return validate_password(password)

    if args.password is not None:
        return validate_password(args.password)

    password = getpass("Password: ")
    repeated = getpass("Repeat password: ")
    if password != repeated:
        raise ManagementUserError("Passwords do not match")
    return validate_password(password)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m management.users",
        description="Manage admin and superuser accounts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin = subparsers.add_parser("create-admin", help="Create admin user")
    create_admin.add_argument("--email", required=True, help="Admin email/login")
    create_admin.add_argument("--name", help="Optional first name")
    create_admin.add_argument("--surname", help="Optional surname")
    add_password_args(create_admin)

    create_su = subparsers.add_parser("create-su", help="Create superuser account")
    create_su.add_argument("--email", required=True, help="Superuser email/login")
    create_su.add_argument("--name", help="Optional first name")
    create_su.add_argument("--surname", help="Optional surname")
    add_password_args(create_su)

    reset_password = subparsers.add_parser("reset-password", help="Reset user password by email/login")
    reset_password.add_argument("--email", required=True, help="User email/login")
    add_password_args(reset_password)

    return parser


async def run_command(args: argparse.Namespace) -> ManagedUserResult:
    password = resolve_password(args)

    async with session_factory() as session:
        try:
            if args.command == "create-admin":
                result = await create_admin_user(
                    session,
                    email=args.email,
                    password=password,
                    is_superuser=False,
                    name=args.name,
                    surname=args.surname,
                )
            elif args.command == "create-su":
                result = await create_admin_user(
                    session,
                    email=args.email,
                    password=password,
                    is_superuser=True,
                    name=args.name,
                    surname=args.surname,
                )
            elif args.command == "reset-password":
                result = await reset_user_password(
                    session,
                    email=args.email,
                    password=password,
                )
            else:
                raise ManagementUserError(f"Unsupported command: {args.command}")

            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


def print_result(command: str, result: ManagedUserResult) -> None:
    action = {
        "create-admin": "Admin user created",
        "create-su": "Superuser created",
        "reset-password": "Password reset",
    }.get(command, "Command completed")

    print(
        f"{action}: id={result.id} email={result.email} "
        f"role={result.role.name} is_superuser={result.is_superuser}"
    )


async def async_main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = await run_command(args)
    except ManagementUserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    finally:
        await engine.dispose()

    print_result(args.command, result)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

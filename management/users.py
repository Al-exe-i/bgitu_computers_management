from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Sequence
from getpass import getpass

from core.exceptions.management import ManagementUserError
from management.runtime import build_managed_users, close_runtime, managed_session
from modules.identity.public import ManagedUserResult, validate_password


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
            raise ManagementUserError(
                f"Environment variable is not set: {args.password_env}"
            )
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

    reset_password = subparsers.add_parser(
        "reset-password", help="Reset user password by email/login"
    )
    reset_password.add_argument("--email", required=True, help="User email/login")
    add_password_args(reset_password)

    return parser


async def run_command(args: argparse.Namespace) -> ManagedUserResult:
    password = resolve_password(args)

    async with managed_session() as session:
        users = build_managed_users(session)
        if args.command in {"create-admin", "create-su"}:
            return await users.create_admin_user(
                email=args.email,
                password=password,
                is_superuser=args.command == "create-su",
                name=args.name,
                surname=args.surname,
            )
        if args.command == "reset-password":
            return await users.reset_user_password(email=args.email, password=password)
        raise ManagementUserError(f"Unsupported command: {args.command}")


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
        await close_runtime()

    print_result(args.command, result)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import BootstrapConfig, BootstrapOfficeConfig, settings
from db.session import engine, session_factory
from management.users import (
    ManagedUserResult,
    ManagementUserError,
    create_admin_user,
    get_user_by_email,
)
from modules.inventory.models.office import Office
from modules.identity.models.user import User

_BOOTSTRAP_ADVISORY_LOCK_ID = 4_244_748_214_403_238_731


class BootstrapError(Exception):
    """Raised when database bootstrap cannot be completed safely."""


@dataclass(slots=True, frozen=True)
class BootstrapResult:
    created_office_ids: tuple[int, ...]
    superuser: ManagedUserResult | None
    superuser_created: bool


async def bootstrap_database(
    session: AsyncSession,
    config: BootstrapConfig,
    *,
    acquire_lock: bool = True,
) -> BootstrapResult:
    if acquire_lock:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": _BOOTSTRAP_ADVISORY_LOCK_ID},
        )

    created_office_ids = await ensure_offices(session, config.offices)
    superuser, superuser_created = await ensure_initial_superuser(session, config)
    return BootstrapResult(
        created_office_ids=tuple(created_office_ids),
        superuser=superuser,
        superuser_created=superuser_created,
    )


async def ensure_offices(
    session: AsyncSession,
    offices: list[BootstrapOfficeConfig],
) -> list[int]:
    created_ids: list[int] = []
    for office_config in offices:
        existing_by_id = await session.get(Office, office_config.id)
        if existing_by_id is not None:
            if existing_by_id.address != office_config.address:
                logger.warning(
                    "Bootstrap office id={} already exists with another address; keeping database value",
                    office_config.id,
                )
            continue

        existing_by_address = await session.scalar(
            select(Office).where(
                func.lower(Office.address) == office_config.address.strip().lower()
            )
        )
        if existing_by_address is not None:
            continue

        session.add(
            Office(
                id=office_config.id,
                address=office_config.address.strip(),
            )
        )
        created_ids.append(office_config.id)

    if created_ids:
        await session.flush()
    return created_ids


async def ensure_initial_superuser(
    session: AsyncSession,
    config: BootstrapConfig,
) -> tuple[ManagedUserResult | None, bool]:
    existing_superuser = await session.scalar(
        select(User).where(User.is_superuser.is_(True)).order_by(User.id).limit(1)
    )
    if existing_superuser is not None:
        return _managed_user_result(existing_superuser), False

    if config.superuser_email is None or config.superuser_password is None:
        if config.require_superuser:
            raise BootstrapError(
                "No superuser exists. Set BGITU__BOOTSTRAP__SUPERUSER_EMAIL and "
                "BGITU__BOOTSTRAP__SUPERUSER_PASSWORD, then run bootstrap again."
            )
        return None, False

    existing_user = await get_user_by_email(session, config.superuser_email)
    if existing_user is not None:
        raise BootstrapError(
            "Bootstrap superuser email belongs to a regular user. "
            "Refusing to elevate the account automatically."
        )

    try:
        result = await create_admin_user(
            session,
            email=config.superuser_email,
            password=config.superuser_password.get_secret_value(),
            is_superuser=True,
            name=config.superuser_name,
            surname=config.superuser_surname,
        )
    except ManagementUserError as exc:
        raise BootstrapError(str(exc)) from exc
    return result, True


def _managed_user_result(user: User) -> ManagedUserResult:
    return ManagedUserResult(
        id=user.id,
        email=user.email,
        role=user.role,
        is_superuser=user.is_superuser,
    )


def print_result(result: BootstrapResult) -> None:
    if result.created_office_ids:
        print(
            "Bootstrap created offices: "
            + ", ".join(str(office_id) for office_id in result.created_office_ids)
        )
    else:
        print("Bootstrap offices: unchanged")

    if result.superuser_created and result.superuser is not None:
        print(
            "Bootstrap created superuser: "
            f"id={result.superuser.id} email={result.superuser.email}"
        )
    elif result.superuser is not None:
        print(
            "Bootstrap superuser: already configured "
            f"(id={result.superuser.id} email={result.superuser.email})"
        )
    else:
        print("Bootstrap superuser: skipped by configuration")


async def async_main() -> int:
    try:
        async with session_factory() as session:
            try:
                result = await bootstrap_database(session, settings.bootstrap)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except (BootstrapError, ManagementUserError) as exc:
        print(f"Bootstrap error: {exc}", file=sys.stderr)
        return 2
    finally:
        await engine.dispose()

    print_result(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m management.bootstrap",
        description="Apply idempotent initial database data.",
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())

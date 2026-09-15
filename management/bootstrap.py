from __future__ import annotations

import argparse
import asyncio
import sys

from core.config import BootstrapConfig, settings
from core.exceptions.management import BootstrapError, ManagementUserError
from management.runtime import build_bootstrap, close_runtime, managed_session
from modules.administration.contracts import BootstrapPlan, BootstrapResult
from modules.identity.public import InitialSuperuser
from modules.inventory.public import InitialOffice


def build_plan(config: BootstrapConfig) -> BootstrapPlan:
    return BootstrapPlan(
        offices=tuple(
            InitialOffice(office.id, office.address) for office in config.offices
        ),
        superuser=InitialSuperuser(
            email=config.superuser_email,
            password=config.superuser_password.get_secret_value()
            if config.superuser_password is not None
            else None,
            name=config.superuser_name,
            surname=config.superuser_surname,
            required=config.require_superuser,
        ),
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
        async with managed_session() as session:
            result = await build_bootstrap(session).execute(
                build_plan(settings.bootstrap)
            )
    except (BootstrapError, ManagementUserError) as exc:
        print(f"Bootstrap error: {exc}", file=sys.stderr)
        return 2
    finally:
        await close_runtime()

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

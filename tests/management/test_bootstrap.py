import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.exceptions.management import BootstrapError
from modules.administration.application.bootstrap import BootstrapUseCase
from modules.administration.contracts import BootstrapPlan
from modules.identity.public import InitialSuperuser, ManagedUserResult, UserRole
from modules.identity.services.management import ManagedUserService
from modules.inventory.public import InitialOffice
from modules.inventory.services.bootstrap import OfficeBootstrapService


@pytest.fixture
def initial_users():
    users = SimpleNamespace(
        get_first_superuser=AsyncMock(return_value=None),
        get_by_email=AsyncMock(return_value=None),
    )
    service = ManagedUserService(users, None, None, on_commit=lambda hook: None)
    service.create_admin_user = AsyncMock(
        return_value=ManagedUserResult(8, "admin@example.ru", UserRole.admin, True)
    )
    return service, users


def test_existing_superuser_is_never_modified(initial_users):
    service, users = initial_users
    users.get_first_superuser.return_value = ManagedUserResult(
        4, "existing@example.ru", UserRole.admin, True
    )
    result, created = asyncio.run(
        service.ensure_initial_superuser(
            InitialSuperuser(email="another@example.ru", password="another-password"),
        )
    )
    assert not created and result.id == 4
    service.create_admin_user.assert_not_awaited()
    users.get_by_email.assert_not_awaited()


def test_empty_database_requires_initial_superuser_credentials(initial_users):
    service, _ = initial_users
    with pytest.raises(BootstrapError, match="No superuser exists"):
        asyncio.run(service.ensure_initial_superuser(InitialSuperuser()))


def test_optional_initial_superuser_can_be_skipped(initial_users):
    service, _ = initial_users
    assert asyncio.run(
        service.ensure_initial_superuser(InitialSuperuser(required=False))
    ) == (None, False)


def test_bootstrap_creates_initial_superuser_once(initial_users):
    service, users = initial_users
    config = InitialSuperuser(email="admin@example.ru", password="strong-password")
    result, created = asyncio.run(service.ensure_initial_superuser(config))
    assert created and result.id == 8
    users.get_first_superuser.return_value = result
    assert asyncio.run(service.ensure_initial_superuser(config)) == (result, False)
    service.create_admin_user.assert_awaited_once()
    assert "strong-password" not in repr(config)


def test_bootstrap_never_promotes_regular_user(initial_users):
    service, users = initial_users
    users.get_by_email.return_value = object()
    with pytest.raises(BootstrapError, match="Refusing to elevate"):
        asyncio.run(
            service.ensure_initial_superuser(
                InitialSuperuser("admin@example.ru", "secret123")
            )
        )
    service.create_admin_user.assert_not_awaited()


def test_offices_keep_existing_values_and_repair_sequence():
    repo = SimpleNamespace(
        lock=AsyncMock(),
        get=AsyncMock(return_value=SimpleNamespace(address="Renamed")),
        get_by_address=AsyncMock(),
        create=AsyncMock(),
        synchronize_sequence=AsyncMock(),
    )
    changes = []
    service = OfficeBootstrapService(repo, on_changed=lambda: changes.append(True))
    assert asyncio.run(service.ensure_offices((InitialOffice(1, "Original"),))) == ()
    repo.lock.assert_awaited_once()
    repo.create.assert_not_awaited()
    repo.synchronize_sequence.assert_awaited_once()
    assert changes == []


def test_office_seed_is_idempotent_even_with_repeated_addresses():
    records = {}

    async def get(office_id):
        return records.get(office_id)

    async def by_address(address):
        return next(
            (row for row in records.values() if row.address.lower() == address.lower()),
            None,
        )

    async def create(office_id, address):
        records[office_id] = SimpleNamespace(address=address)

    repo = SimpleNamespace(
        lock=AsyncMock(),
        get=get,
        get_by_address=by_address,
        create=create,
        synchronize_sequence=AsyncMock(),
    )
    changes = []
    service = OfficeBootstrapService(repo, on_changed=lambda: changes.append(True))
    offices = (InitialOffice(1, " First "), InitialOffice(2, "FIRST"))
    assert asyncio.run(service.ensure_offices(offices)) == (1,)
    assert asyncio.run(service.ensure_offices(offices)) == ()
    assert len(records) == 1 and changes == [True]


def test_bootstrap_acquires_lock_before_any_changes():
    calls = []

    async def acquire():
        calls.append("lock")

    async def offices(_):
        calls.append("offices")
        return (1,)

    async def users(_):
        calls.append("users")
        raise BootstrapError("missing credentials")

    use_case = BootstrapUseCase(
        SimpleNamespace(ensure_initial_superuser=users),
        SimpleNamespace(ensure_offices=offices),
        SimpleNamespace(acquire=acquire),
    )
    with pytest.raises(BootstrapError):
        asyncio.run(use_case.execute(BootstrapPlan((), InitialSuperuser())))
    assert calls == ["lock", "offices", "users"]

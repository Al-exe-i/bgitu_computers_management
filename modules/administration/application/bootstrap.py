from typing import Protocol

from modules.administration.contracts import BootstrapPlan, BootstrapResult
from modules.identity.public import InitialUserProvisioner
from modules.inventory.public import OfficeProvisioner


class BootstrapLock(Protocol):
    async def acquire(self) -> None: ...


class BootstrapUseCase:
    def __init__(
        self,
        users: InitialUserProvisioner,
        offices: OfficeProvisioner,
        lock: BootstrapLock,
    ):
        self.users = users
        self.offices = offices
        self.lock = lock

    async def execute(self, plan: BootstrapPlan) -> BootstrapResult:
        await self.lock.acquire()
        office_ids = await self.offices.ensure_offices(plan.offices)
        user, created = await self.users.ensure_initial_superuser(plan.superuser)
        return BootstrapResult(office_ids, user, created)

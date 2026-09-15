from collections.abc import Callable

from loguru import logger

from core.exceptions.management import BootstrapError
from modules.inventory.bootstrap_contracts import InitialOffice
from modules.inventory.repositories.bootstrap import OfficeBootstrapRepository


class OfficeBootstrapService:
    def __init__(
        self, repo: OfficeBootstrapRepository, *, on_changed: Callable[[], None]
    ):
        self.repo = repo
        self.on_changed = on_changed

    async def ensure_offices(
        self, offices: tuple[InitialOffice, ...]
    ) -> tuple[int, ...]:
        if not offices:
            return ()
        seen_ids = set()
        for office in offices:
            if (
                office.id <= 0
                or office.id in seen_ids
                or not office.address.strip()
                or len(office.address.strip()) > 100
            ):
                raise BootstrapError("Invalid or duplicate bootstrap office")
            seen_ids.add(office.id)
        await self.repo.lock()
        created = []
        for office in offices:
            existing = await self.repo.get(office.id)
            if existing is not None:
                if existing.address != office.address.strip():
                    logger.warning(
                        "Bootstrap office id={} has another address; keeping database value",
                        office.id,
                    )
                continue
            if await self.repo.get_by_address(office.address.strip()) is not None:
                continue
            await self.repo.create(office.id, office.address.strip())
            created.append(office.id)
        await self.repo.synchronize_sequence()
        if created:
            self.on_changed()
        return tuple(created)

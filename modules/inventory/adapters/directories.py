from modules.inventory.public import AudienceContext, OfficeContext
from modules.inventory.repositories.audiences import AudienceRepository
from modules.inventory.repositories.offices import OfficeRepository


class AudienceDirectoryReader:
    def __init__(self, repo: AudienceRepository) -> None:
        self.repo = repo

    async def get_one_short(self, audience_id: int) -> AudienceContext | None:
        row = await self.repo.get_one_short(audience_id)
        if row is None:
            return None
        return AudienceContext(row.id, row.public_id, row.number, row.office_id)


class OfficeDirectoryReader:
    def __init__(self, repo: OfficeRepository) -> None:
        self.repo = repo

    async def get_one_short(self, office_id: int) -> OfficeContext | None:
        row = await self.repo.get_one_short(office_id)
        return OfficeContext(row.id, row.address) if row is not None else None

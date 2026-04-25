from typing import Sequence
from models import Office
from repositories.office_repo import OfficeRepository
from schemas.office import OfficeResponse, OfficeUpdate, OfficeShort, OfficeCreate


class OfficeService:
    def __init__(self, repo: OfficeRepository):
        self.repo = repo

    async def get_all(self) -> Sequence[OfficeResponse | OfficeShort]:
        return await self.repo.get_list()

    async def get_all_short(self) -> Sequence[OfficeShort]:
        return await self.repo.get_list_short()

    async def get(self, office_id: int) -> OfficeResponse | None:
        return await self.repo.get_one(office_id)

    async def get_short(self, office_id: int) -> OfficeShort | None:
        return await self.repo.get_one_short(office_id)

    async def create(self, office: OfficeCreate) -> Office:
        new_office = Office(**office.model_dump())
        return await self.repo.create(new_office)

    async def update(self, schema: OfficeUpdate, orm_model: OfficeShort) -> Office:
        return await self.repo.update(schema, orm_model)

    async def delete(self, office_id: int) -> bool:
        office = await self.repo.get_one(office_id)
        if not office:
            return False
        return await self.repo.delete(office)

    async def count_faulty(self, office_id: int) -> int:
        return await self.repo.count_faulty_computers(office_id)
from typing import Sequence

from sqlalchemy.exc import IntegrityError

from core.exceptions import OfficeAlreadyExistsError
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
        try:
            return await self.repo.create(new_office)
        except IntegrityError as exc:
            raise OfficeAlreadyExistsError() from exc

    async def update(self, office_id: int, schema: OfficeUpdate) -> Office | None:
        office = await self.repo.get_one_short(office_id)
        if not office:
            return None
        return await self.repo.update(schema, office)

    async def delete(self, office_id: int) -> bool:
        office = await self.repo.get_one(office_id)
        if not office:
            return False
        return await self.repo.delete(office)


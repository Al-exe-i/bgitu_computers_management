from typing import Sequence

from sqlalchemy.exc import IntegrityError

from core.exceptions import OfficeAlreadyExistsError
from models import Office
from repositories.office_repo import OfficeRepository
from schemas.office import OfficeResponse, OfficeUpdate, OfficeShort, OfficeCreate
from schemas.analytics import HardwareAnalyticsFilterOptions
from services.cache_invalidation import invalidate_after_commit
from services.response_cache import RedisTypedCache


class OfficeService:
    def __init__(
        self,
        repo: OfficeRepository,
        office_short_cache: RedisTypedCache[list[OfficeShort]] | None = None,
        analytics_filter_options_cache: RedisTypedCache[HardwareAnalyticsFilterOptions] | None = None,
    ):
        self.repo = repo
        self.office_short_cache = office_short_cache
        self.analytics_filter_options_cache = analytics_filter_options_cache

    async def get_all(self) -> Sequence[OfficeResponse | OfficeShort]:
        return await self.repo.get_list()

    async def get_all_short(self) -> Sequence[OfficeShort]:
        if self.office_short_cache is not None:
            cached = await self.office_short_cache.get()
            if cached is not None:
                return cached

        offices = [
            OfficeShort.model_validate(office)
            for office in await self.repo.get_list_short()
        ]

        if self.office_short_cache is not None:
            await self.office_short_cache.set(offices)

        return offices

    async def get(self, office_id: int) -> OfficeResponse | None:
        return await self.repo.get_one(office_id)

    async def get_short(self, office_id: int) -> OfficeShort | None:
        return await self.repo.get_one_short(office_id)

    async def create(self, office: OfficeCreate) -> Office:
        new_office = Office(**office.model_dump())
        try:
            created = await self.repo.create(new_office)
        except IntegrityError as exc:
            raise OfficeAlreadyExistsError() from exc
        self._invalidate_related_caches_after_commit()
        return created

    async def update(self, office_id: int, schema: OfficeUpdate) -> Office | None:
        office = await self.repo.get_one_short(office_id)
        if not office:
            return None
        updated = await self.repo.update(schema, office)
        self._invalidate_related_caches_after_commit()
        return updated

    async def delete(self, office_id: int) -> bool:
        office = await self.repo.get_one(office_id)
        if not office:
            return False
        deleted = await self.repo.delete(office)
        if deleted:
            self._invalidate_related_caches_after_commit()
        return deleted

    def _invalidate_related_caches_after_commit(self) -> None:
        invalidate_after_commit(
            self.repo,
            self.office_short_cache,
            self.analytics_filter_options_cache,
        )


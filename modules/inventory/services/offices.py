from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError

from core.exceptions import OfficeAlreadyExistsError
from modules.inventory.models.office import Office
from modules.inventory.repositories.offices import OfficeRepository
from modules.inventory.schemas.analytics import HardwareAnalyticsFilterOptions
from modules.inventory.schemas.office import (
    OfficeCreate,
    OfficeResponse,
    OfficeShort,
    OfficeUpdate,
)
from modules.inventory.services.cache import (
    AfterCommit,
    after_commit,
    invalidate_after_commit,
)
from services.response_cache import RedisTypedCache


class OfficeService:
    def __init__(
        self,
        repo: OfficeRepository,
        office_short_cache: RedisTypedCache[list[OfficeShort]] | None = None,
        analytics_filter_options_cache: RedisTypedCache[HardwareAnalyticsFilterOptions]
        | None = None,
        *,
        on_commit: AfterCommit | None = None,
    ):
        self.repo = repo
        self.on_commit = on_commit
        self.office_short_cache = office_short_cache
        self.analytics_filter_options_cache = analytics_filter_options_cache

    async def get_all(self) -> Sequence[OfficeResponse | OfficeShort]:
        return [
            OfficeResponse.model_validate(row, from_attributes=True)
            for row in await self.repo.get_list()
        ]

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
            snapshot = [office.model_copy(deep=True) for office in offices]
            after_commit(self.on_commit, lambda: self.office_short_cache.set(snapshot))

        return offices

    async def get(self, office_id: int) -> OfficeResponse | None:
        office = await self.repo.get_one(office_id)
        return (
            OfficeResponse.model_validate(office, from_attributes=True)
            if office
            else None
        )

    async def get_short(self, office_id: int) -> OfficeShort | None:
        office = await self.repo.get_one_short(office_id)
        return (
            OfficeShort.model_validate(office, from_attributes=True) if office else None
        )

    async def create(self, office: OfficeCreate) -> OfficeShort:
        new_office = Office(**office.model_dump())
        try:
            created = await self.repo.create(new_office)
        except IntegrityError as exc:
            raise OfficeAlreadyExistsError() from exc
        self._invalidate_related_caches_after_commit()
        return OfficeShort.model_validate(created, from_attributes=True)

    async def update(self, office_id: int, schema: OfficeUpdate) -> OfficeShort | None:
        office = await self.repo.get_one_short(office_id)
        if not office:
            return None
        updated = await self.repo.update(schema, office)
        self._invalidate_related_caches_after_commit()
        return OfficeShort.model_validate(updated, from_attributes=True)

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
            self.on_commit,
            self.office_short_cache,
            self.analytics_filter_options_cache,
        )

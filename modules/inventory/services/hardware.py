from collections.abc import Sequence
from typing import Protocol

from core.exceptions import HardwareNotFoundError
from modules.inventory.models.hardware import Hardware
from modules.inventory.repositories.hardware import HardwareRepository
from modules.inventory.schemas.hardware import (
    HardwareFullResponse,
    HardwareGridItem,
    HardwareUpdate,
)
from modules.inventory.schemas.office import OfficeShort
from modules.inventory.services.cache import AfterCommit, invalidate_after_commit
from modules.inventory.services.hw_specs import validate_specs
from services.response_cache import RedisTypedCache


class HardwareGridPort(Protocol):
    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]: ...
    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware: ...
    async def delete(self, hardware_id: int) -> None: ...


class HardwareService:
    def __init__(
        self,
        repo: HardwareRepository,
        office_short_cache: RedisTypedCache[list[OfficeShort]] | None = None,
        *,
        on_commit: AfterCommit | None = None,
    ):
        self.repo = repo
        self.on_commit = on_commit
        self.office_short_cache = office_short_cache

    async def get(self, hardware_id: int) -> HardwareFullResponse | None:
        hardware = await self.repo.get_by_id(hardware_id)
        return HardwareFullResponse.model_validate(hardware, from_attributes=True) if hardware else None

    async def update(self, hardware_id: int, schema: HardwareUpdate) -> HardwareFullResponse:
        hardware = await self.repo.get_by_id(hardware_id)
        if not hardware:
            raise HardwareNotFoundError()

        update_data = schema.model_dump(exclude_unset=True, exclude={"files"})
        target_type = update_data.get("type", hardware.type)

        if "specs" in update_data:
            update_data["specs"] = validate_specs(target_type, update_data["specs"])
        elif "type" in update_data:
            update_data["specs"] = validate_specs(target_type, hardware.specs)

        updated = await self.repo.update(hardware_id, update_data)
        if updated is None:
            raise HardwareNotFoundError()
        self._invalidate_related_caches_after_commit()
        return HardwareFullResponse.model_validate(updated, from_attributes=True)

    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]:
        return await self.repo.get_by_audience_id(audience_id)

    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware:
        data = item.model_dump(exclude={"id"})
        data["specs"] = validate_specs(item.type, data.get("specs"))
        hw = Hardware(**data, audience_id=audience_id)
        created = await self.repo.create(hw)
        self._invalidate_related_caches_after_commit()
        return created

    async def delete(self, hardware_id: int) -> None:
        await self.repo.delete(hardware_id)
        self._invalidate_related_caches_after_commit()

    def _invalidate_related_caches_after_commit(self) -> None:
        invalidate_after_commit(self.on_commit, self.office_short_cache)

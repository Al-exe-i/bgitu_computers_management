from typing import Protocol, Sequence

from core.exceptions import HardwareNotFoundError
from models import Hardware
from repositories.hardware_repo import HardwareRepository
from schemas.hardware import HardwareGridItem, HardwareUpdate
from utils.hw_specs import validate_specs


class HardwareGridPort(Protocol):
    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]: ...
    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware: ...
    async def delete(self, hardware_id: int) -> None: ...


class HardwareService:
    def __init__(self, repo: HardwareRepository):
        self.repo = repo

    async def get(self, hardware_id: int):
        return await self.repo.get_by_id(hardware_id)

    async def update(self, hardware_id: int, schema: HardwareUpdate):
        hardware = await self.repo.get_by_id(hardware_id)
        if not hardware:
            raise HardwareNotFoundError()

        update_data = schema.model_dump(exclude_unset=True, exclude={"files"})
        target_type = update_data.get("type", hardware.type)

        if "specs" in update_data:
            update_data["specs"] = validate_specs(target_type, update_data["specs"])
        elif "type" in update_data:
            update_data["specs"] = validate_specs(target_type, hardware.specs)

        if update_data.get("state"):
            update_data["description"] = None

        return await self.repo.update(hardware_id, update_data)

    async def list_by_audience(self, audience_id: int) -> Sequence[Hardware]:
        return await self.repo.get_by_audience_id(audience_id)

    async def create_in_audience(self, audience_id: int, item: HardwareGridItem) -> Hardware:
        data = item.model_dump(exclude={"id"})
        data["specs"] = validate_specs(item.type, data.get("specs"))
        hw = Hardware(**data, audience_id=audience_id)
        return await self.repo.create(hw)

    async def delete(self, hardware_id: int) -> None:
        await self.repo.delete(hardware_id)

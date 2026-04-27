from collections.abc import Sequence

from core.exceptions import AudienceHardwareNotFoundError
from models import Hardware
from schemas.hardware import HardwareGridItem
from services.hardware_service import HardwareGridPort
from utils.grid_utils import GridHelper


class AudienceGridService:
    def __init__(self, hardware: HardwareGridPort) -> None:
        self.hardware = hardware

    def validate(self, items: Sequence[HardwareGridItem], width: int, height: int) -> None:
        GridHelper.validate_grid(items, width, height)

    def build_hardware_models(self, items: Sequence[HardwareGridItem]) -> list[Hardware]:
        return [Hardware(**item.model_dump(exclude={"id"})) for item in items]

    async def sync(self, audience_id: int, incoming: Sequence[HardwareGridItem]) -> None:
        existing_hw_list = await self.hardware.list_by_audience(audience_id)
        existing_map: dict[int, Hardware] = {hw.id: hw for hw in existing_hw_list}
        incoming_existing_ids: set[int] = set()

        for item in incoming:
            if item.id is None:
                await self.hardware.create_in_audience(audience_id, item)
                continue

            db_item = existing_map.get(item.id)
            if db_item is None:
                raise AudienceHardwareNotFoundError(
                    hardware_id=item.id,
                    audience_id=audience_id,
                )

            GridHelper.apply_grid_item(db_item, item)
            incoming_existing_ids.add(item.id)

        for hw_id in existing_map.keys():
            if hw_id not in incoming_existing_ids:
                await self.hardware.delete(hw_id)

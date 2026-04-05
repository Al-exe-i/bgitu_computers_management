from typing import Sequence
from core.exceptions import HTTP404, HTTP400
from models import Hardware, Audience
from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceCreate, AudienceUpdate, AudienceResponse
from schemas.hardware import HardwareGridItem
from services.hardware_service import HardwareGridPort
from utils.audience_landmarks import normalize_landmarks
from utils.grid_utils import GridHelper


class AudienceService:
    def __init__(self, repo: AudienceRepository, hardware: HardwareGridPort):
        self.repo = repo
        self.hardware = hardware

    async def get_list(self) -> Sequence[AudienceResponse]:
        audiences = await self.repo.get_all()
        return [
            AudienceResponse.model_validate(a, from_attributes=True)
            for a in audiences
        ]

    async def get_one(self, audience_id: int):
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            raise HTTP404("Audience not found")
        return audience

    async def create_audience(self, schema: AudienceCreate):
        GridHelper.validate_grid(schema.hardware, schema.width, schema.height)

        audience_data = schema.model_dump(exclude={'hardware'})
        hardware_orm_list = [
            Hardware(**hw.model_dump(exclude={'id'})) for hw in schema.hardware
        ]

        audience_orm = Audience(
            **audience_data,
            hardware=hardware_orm_list
        )

        return await self.repo.create(audience_orm)

    async def update_audience(self, audience_id: int, schema: AudienceUpdate):
        current_audience = await self.repo.get_by_id(audience_id)
        if not current_audience:
            raise HTTP404("Audience not found")

        update_data = schema.model_dump(exclude_unset=True, exclude={'hardware'})

        if "landmarks" in update_data:
            update_data["landmarks"] = normalize_landmarks(update_data["landmarks"])

        target_width = update_data.get("width", current_audience.width)
        target_height = update_data.get("height", current_audience.height)

        if schema.hardware is not None:
            GridHelper.validate_grid(schema.hardware, target_width, target_height)

        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            await self.repo.session.flush()

        if schema.hardware is not None:
            await self._sync_grid(audience_id, schema.hardware)

        await self.repo.session.flush()
        return await self.repo.get_by_id(audience_id)

    async def delete_audience(self, audience_id: int) -> None:
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)

    async def _sync_grid(self, audience_id: int, incoming: Sequence[HardwareGridItem]) -> None:
        existing_hw_list = await self.hardware.list_by_audience(audience_id)
        existing_map: dict[int, Hardware] = {hw.id: hw for hw in existing_hw_list}

        incoming_existing_ids: set[int] = set()

        for item in incoming:
            if item.id is None:
                await self.hardware.create_in_audience(audience_id, item)
                continue

            db_item = existing_map.get(item.id)
            if db_item is None:
                raise HTTP400(f"Hardware id={item.id} not found in audience {audience_id}")

            GridHelper.apply_grid_item(db_item, item)
            incoming_existing_ids.add(item.id)

        for hw_id in existing_map.keys():
            if hw_id not in incoming_existing_ids:
                await self.hardware.delete(hw_id)
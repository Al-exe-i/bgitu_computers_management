from typing import Sequence
from core.exceptions import HTTP404, HTTP400
from models import Hardware, Audience
from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceCreate, AudienceUpdate, AudienceResponse
from schemas.hardware import HardwareGridItem
from services.hardware_service import HardwareGridPort


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

        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            await self.repo.session.flush()

        # Синхронизируем сетку оборудования (если она пришла)
        if schema.hardware is not None:
            await self._sync_grid(audience_id, schema.hardware)

        await self.repo.session.flush()

        await self.repo.session.refresh(current_audience)
        return current_audience

    async def _sync_grid(self, audience_id: int, incoming: Sequence[HardwareGridItem]) -> None:
        existing_hw_list = await self.hardware.list_by_audience(audience_id)
        existing_map: dict[int, Hardware] = {hw.id: hw for hw in existing_hw_list}

        incoming_existing_ids: set[int] = set()

        for item in incoming:
            if item.id is None:
                # Создать новое
                await self.hardware.create_in_audience(audience_id, item)
                continue

            db_item = existing_map.get(item.id)
            if db_item is None:
                # id прислали, но в этой аудитории такого hardware нет
                raise HTTP400(f"Hardware id={item.id} not found in audience {audience_id}")

            # обновить существующее
            db_item.x = item.x
            db_item.y = item.y
            db_item.type = item.type
            db_item.state = item.state

            incoming_existing_ids.add(item.id)

        # Удалить то, чего нет во входящем списке (среди существующих)
        for hw_id in existing_map.keys():
            if hw_id not in incoming_existing_ids:
                await self.hardware.delete(hw_id)

    async def delete_audience(self, audience_id: int):
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)

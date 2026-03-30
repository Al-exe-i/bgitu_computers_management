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
        self._validate_grid(schema.hardware, schema.width, schema.height)

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

        target_width = update_data.get("width", current_audience.width)
        target_height = update_data.get("height", current_audience.height)

        if schema.hardware is not None:
            self._validate_grid(schema.hardware, target_width, target_height)

        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            await self.repo.session.flush()

        if schema.hardware is not None:
            await self._sync_grid(audience_id, schema.hardware)

        await self.repo.session.flush()
        await self.repo.session.refresh(current_audience)
        return current_audience

    async def delete_audience(self, audience_id: int):
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

            self._apply_grid_item(db_item, item)
            incoming_existing_ids.add(item.id)

        for hw_id in existing_map.keys():
            if hw_id not in incoming_existing_ids:
                await self.hardware.delete(hw_id)

    def _rectangles_intersect(self, a: HardwareGridItem, b: HardwareGridItem) -> bool:
        return not (
                a.x + a.width <= b.x or
                b.x + b.width <= a.x or
                a.y + a.height <= b.y or
                b.y + b.height <= a.y
        )

    def _validate_item_bounds(self, item: HardwareGridItem, grid_width: int, grid_height: int) -> None:
        if item.x < 0 or item.y < 0:
            raise HTTP400("Hardware coordinates must be non-negative")

        if item.x + item.width > grid_width:
            raise HTTP400(
                f"Hardware id={item.id or 'new'} exceeds audience width: "
                f"x={item.x}, width={item.width}, audience_width={grid_width}"
            )

        if item.y + item.height > grid_height:
            raise HTTP400(
                f"Hardware id={item.id or 'new'} exceeds audience height: "
                f"y={item.y}, height={item.height}, audience_height={grid_height}"
            )

    def _validate_grid(self, items: Sequence[HardwareGridItem], grid_width: int, grid_height: int) -> None:
        seen_ids: set[int] = set()

        for item in items:
            self._validate_item_bounds(item, grid_width, grid_height)

            if item.id is not None:
                if item.id in seen_ids:
                    raise HTTP400(f"Duplicate hardware id={item.id} in payload")
                seen_ids.add(item.id)

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if self._rectangles_intersect(items[i], items[j]):
                    raise HTTP400(
                        f"Hardware items intersect: "
                        f"{items[i].id or 'new'} and {items[j].id or 'new'}"
                    )

    def _apply_grid_item(self, db_item: Hardware, item: HardwareGridItem) -> None:
        db_item.x = item.x
        db_item.y = item.y
        db_item.width = item.width
        db_item.height = item.height
        db_item.type = item.type
        db_item.state = item.state
        db_item.description = item.description
        db_item.inv_number = item.inv_number
        db_item.title = item.title
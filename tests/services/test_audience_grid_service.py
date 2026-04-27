import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import AudienceHardwareNotFoundError
from models.hardware import HardwareType
from schemas.hardware import HardwareGridItem
from services.audience_grid_service import AudienceGridService


class FakeHardwareGrid:
    def __init__(self, hardware: list[SimpleNamespace]) -> None:
        self.hardware = hardware
        self.created: list[tuple[int, HardwareGridItem]] = []
        self.deleted: list[int] = []

    async def list_by_audience(self, audience_id: int):
        return self.hardware

    async def create_in_audience(self, audience_id: int, item: HardwareGridItem):
        self.created.append((audience_id, item))
        return SimpleNamespace(id=100, audience_id=audience_id, **item.model_dump(exclude={"id"}))

    async def delete(self, hardware_id: int) -> None:
        self.deleted.append(hardware_id)


def make_item(
    *,
    item_id: int | None = None,
    x: int = 0,
    y: int = 0,
) -> HardwareGridItem:
    return HardwareGridItem(
        id=item_id,
        type=HardwareType.computer,
        x=x,
        y=y,
        state=True,
        specs={},
    )


def make_hardware(hardware_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=hardware_id,
        type=HardwareType.computer,
        x=0,
        y=0,
        width=1,
        height=1,
        state=True,
        description=None,
        inv_number=None,
        title=None,
        specs={},
    )


def test_sync_updates_existing_creates_new_and_deletes_missing() -> None:
    async def scenario() -> None:
        existing = [make_hardware(1), make_hardware(2)]
        hardware = FakeHardwareGrid(existing)
        service = AudienceGridService(hardware)

        await service.sync(
            12,
            [
                make_item(item_id=1, x=3, y=4),
                make_item(x=1, y=1),
            ],
        )

        assert existing[0].x == 3
        assert existing[0].y == 4
        assert len(hardware.created) == 1
        assert hardware.created[0][0] == 12
        assert hardware.deleted == [2]

    asyncio.run(scenario())


def test_sync_rejects_hardware_from_another_audience() -> None:
    async def scenario() -> None:
        hardware = FakeHardwareGrid([])
        service = AudienceGridService(hardware)

        with pytest.raises(AudienceHardwareNotFoundError, match="Hardware id=99"):
            await service.sync(12, [make_item(item_id=99)])

        assert hardware.created == []
        assert hardware.deleted == []

    asyncio.run(scenario())

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from modules.inventory.application.floor_plans import InventoryFloorPlanUseCases
from modules.inventory.repositories.floor_plans import FloorPlanRepository
from modules.inventory.schemas.floor_plan import FloorInfo
from modules.inventory.schemas.office import OfficeUpdate
from modules.inventory.services.floor_plans import FloorPlanService


@pytest.mark.parametrize(
    "schema, data",
    [
        (FloorInfo, {"name": "x" * 121}),
        (FloorInfo, {"description": "x" * 4001}),
        (FloorInfo, {"positions": {}}),
        (OfficeUpdate, {"internet_provider": "x" * 121}),
    ],
)
def test_location_info_rejects_invalid_fields(schema, data):
    with pytest.raises(ValidationError):
        schema(**data)


def test_partial_floor_info_update_preserves_geometry_and_omitted_fields():
    plan = SimpleNamespace(
        name="Название",
        description="Описание",
        width=20,
        height=12,
        revision=4,
        positions={"room": {"x": 1}},
        landmarks={"north": "Вход"},
    )
    session = SimpleNamespace(flush=AsyncMock())
    repo = FloorPlanRepository(session)
    repo.get = AsyncMock(return_value=plan)
    service = FloorPlanService(repo)
    before = vars(plan).copy()
    result = asyncio.run(service.update_info(1, 2, FloorInfo(description=None)))
    assert result == FloorInfo(name="Название", description=None)
    assert vars(plan) == {**before, "description": None}
    repo.get.assert_awaited_once_with(1, 2, for_update=True)
    session.flush.assert_awaited_once()


def test_unsaved_floor_info_does_not_write():
    repo = SimpleNamespace(get=AsyncMock(return_value=None))
    assert asyncio.run(FloorPlanService(repo).get_info(1, 2)) == FloorInfo()
    repo.get.assert_awaited_once_with(1, 2)


def test_floor_info_audit_does_not_store_description():
    service = SimpleNamespace(
        update_info=AsyncMock(return_value=FloorInfo(description="Описание"))
    )
    audit = SimpleNamespace(log=AsyncMock())
    asyncio.run(
        InventoryFloorPlanUseCases(service).update_info(
            1, 2, FloorInfo(description="Описание"), audit
        )
    )
    assert audit.log.await_args.kwargs["payload"] == {
        "floor": 2,
        "changed_fields": ["description"],
    }


def test_office_optional_fields_can_be_cleared_without_overwriting_address():
    assert OfficeUpdate(internet_provider=None).model_dump(exclude_unset=True) == {
        "internet_provider": None
    }

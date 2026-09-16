import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from core.exceptions.floor_plan import FloorPlanConflictError, FloorPlanRoomError
from modules.inventory.application.floor_plans import InventoryFloorPlanUseCases
from modules.inventory.schemas.audience import AudienceCreate, AudienceUpdate
from modules.inventory.schemas.floor_plan import FloorPlanUpdate
from modules.inventory.services.audiences import AudienceService
from modules.inventory.services.floor_plans import FloorPlanService
from modules.inventory.types import RoomType


def placement(public_id=None, **kwargs):
    return dict(
        audience_public_id=public_id or uuid4(), x=0, y=0, width=2, height=2, **kwargs
    )


@pytest.mark.parametrize(
    "rooms",
    [
        [{"audience_public_id": uuid4(), "x": -1, "y": 0, "width": 1, "height": 1}],
        [{"audience_public_id": uuid4(), "x": 4, "y": 0, "width": 2, "height": 1}],
        [placement(), placement()],
        [{"audience_public_id": uuid4(), "x": True, "y": 0, "width": 1, "height": 1}],
    ],
)
def test_invalid_geometry_is_rejected(rooms):
    with pytest.raises(ValidationError):
        FloorPlanUpdate(revision=0, width=5, height=5, rooms=rooms)


def test_duplicate_rooms_are_rejected_even_without_overlap():
    room = placement()
    with pytest.raises(ValidationError):
        FloorPlanUpdate(revision=0, width=5, height=5, rooms=[room, {**room, "x": 3}])


def test_old_audience_payload_defaults_to_educational_and_null_update_is_rejected():
    room = AudienceCreate(number=101, floor=1, office_id=1, width=5, height=5)
    assert room.room_type == RoomType.educational
    assert "room_type" not in AudienceUpdate(description="New").model_dump(
        exclude_unset=True
    )
    assert (
        AudienceUpdate(room_type="administrative").room_type == RoomType.administrative
    )
    with pytest.raises(ValidationError):
        AudienceUpdate(room_type=None)


@pytest.fixture
def floor_plan():
    room = SimpleNamespace(
        public_id=uuid4(), number=101, room_type=RoomType.educational, description=None
    )
    plan = SimpleNamespace(width=20, height=12, revision=0, positions={}, landmarks={})

    async def save(plan, width, height, positions, landmarks):
        plan.width, plan.height, plan.positions = width, height, positions
        plan.landmarks = landmarks
        plan.revision += 1

    repo = SimpleNamespace(
        get=AsyncMock(return_value=plan),
        list_rooms=AsyncMock(return_value=[room]),
        save=AsyncMock(side_effect=save),
    )
    return FloorPlanService(repo), repo, room


def test_unsaved_floor_has_unplaced_rooms_without_writing(floor_plan):
    service, repo, room = floor_plan
    repo.get.return_value = None
    result = asyncio.run(service.get(1, 2))
    assert (result.width, result.height, result.revision) == (20, 12, 0)
    assert result.rooms[0].audience_public_id == room.public_id
    assert result.rooms[0].placement is None
    repo.save.assert_not_awaited()


def test_save_and_clear_positions_do_not_delete_rooms(floor_plan):
    service, repo, room = floor_plan
    data = FloorPlanUpdate(
        revision=0, width=5, height=5, rooms=[placement(room.public_id)]
    )
    result = asyncio.run(service.update(1, 2, data))
    assert result.revision == 1 and result.rooms[0].placement.x == 0
    repo.get.assert_awaited_with(1, 2, for_update=True)
    result = asyncio.run(
        service.update(1, 2, FloorPlanUpdate(revision=1, width=5, height=5, rooms=[]))
    )
    assert (
        result.revision == 2
        and len(result.rooms) == 1
        and result.rooms[0].placement is None
    )


def test_stale_revision_cannot_overwrite_plan(floor_plan):
    service, repo, _ = floor_plan
    repo.get.return_value.revision = 3
    with pytest.raises(FloorPlanConflictError):
        asyncio.run(
            service.update(
                1, 2, FloorPlanUpdate(revision=2, width=5, height=5, rooms=[])
            )
        )
    repo.save.assert_not_awaited()


def test_foreign_room_is_rejected(floor_plan):
    service, repo, _ = floor_plan
    with pytest.raises(FloorPlanRoomError):
        asyncio.run(
            service.update(
                1,
                2,
                FloorPlanUpdate(revision=0, width=5, height=5, rooms=[placement()]),
            )
        )
    repo.save.assert_not_awaited()


def test_landmarks_are_saved_preserved_for_old_clients_and_cleared(floor_plan):
    service, repo, _ = floor_plan
    result = asyncio.run(service.update(1, 2, FloorPlanUpdate(
        revision=0, width=20, height=12, rooms=[], landmarks={"north": "  Лестница  "}
    )))
    assert result.landmarks.north == "Лестница"
    assert repo.get.return_value.landmarks["north"] == "Лестница"
    result = asyncio.run(service.update(1, 2, FloorPlanUpdate(
        revision=1, width=20, height=12, rooms=[]
    )))
    assert result.landmarks.north == "Лестница"
    result = asyncio.run(service.update(1, 2, FloorPlanUpdate(
        revision=2, width=20, height=12, rooms=[], landmarks={}
    )))
    assert result.landmarks.north == ""
    assert result.revision == 3


@pytest.mark.parametrize("landmarks", [{"north": "x" * 129}, {"unknown": "text"}, {"east": None}, None])
def test_invalid_landmarks_are_rejected(landmarks):
    with pytest.raises(ValidationError):
        FloorPlanUpdate(revision=0, width=20, height=12, rooms=[], landmarks=landmarks)


def test_audit_omits_layout_payload(floor_plan):
    service, _, room = floor_plan
    audit = SimpleNamespace(log=AsyncMock())
    data = FloorPlanUpdate(
        revision=0, width=5, height=5, rooms=[placement(room.public_id)]
    )
    asyncio.run(InventoryFloorPlanUseCases(service).update(1, 2, data, audit))
    payload = audit.log.call_args.kwargs["payload"]
    assert payload == {
        "floor": 2,
        "width": 5,
        "height": 5,
        "rooms_count": 1,
        "revision": 1,
    }


@pytest.mark.parametrize(
    "changes, removed",
    [({"floor": 3}, True), ({"office_id": 2}, True), ({"description": "New"}, False)],
)
def test_room_move_removes_placement_but_edit_keeps_it(changes, removed):
    room = SimpleNamespace(
        id=1,
        public_id=uuid4(),
        number=101,
        floor=2,
        office_id=1,
        room_type=RoomType.educational,
        description=None,
        width=5,
        height=5,
        landmarks={},
        hardware=[],
    )
    repo = SimpleNamespace(
        get_by_id=AsyncMock(return_value=room),
        flush=AsyncMock(),
        remove_floor_placement=AsyncMock(),
    )
    asyncio.run(
        AudienceService(repo, SimpleNamespace()).update_audience(
            1, AudienceUpdate(**changes)
        )
    )
    if removed:
        repo.remove_floor_placement.assert_awaited_once_with(room.public_id)
    else:
        repo.remove_floor_placement.assert_not_awaited()

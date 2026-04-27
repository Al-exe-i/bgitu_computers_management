import pytest

from core.exceptions import AudienceGridValidationError
from models.hardware import HardwareType
from schemas.hardware import HardwareGridItem
from utils.grid_utils import GridHelper


def make_item(
    *,
    item_id: int | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 1,
    height: int = 1,
) -> HardwareGridItem:
    return HardwareGridItem(
        id=item_id,
        type=HardwareType.computer,
        x=x,
        y=y,
        width=width,
        height=height,
        state=True,
        specs={},
    )


def test_validate_grid_accepts_non_intersecting_items() -> None:
    items = [
        make_item(item_id=1, x=0, y=0),
        make_item(item_id=2, x=1, y=0),
        make_item(item_id=3, x=0, y=1, width=2),
    ]

    GridHelper.validate_grid(items, grid_width=4, grid_height=4)


def test_validate_grid_rejects_intersection() -> None:
    items = [
        make_item(item_id=1, x=0, y=0, width=2, height=2),
        make_item(item_id=2, x=1, y=1, width=2, height=2),
    ]

    with pytest.raises(AudienceGridValidationError, match="intersect"):
        GridHelper.validate_grid(items, grid_width=5, grid_height=5)


def test_validate_grid_rejects_duplicate_ids() -> None:
    items = [
        make_item(item_id=7, x=0, y=0),
        make_item(item_id=7, x=1, y=0),
    ]

    with pytest.raises(AudienceGridValidationError, match="Duplicate hardware id=7"):
        GridHelper.validate_grid(items, grid_width=5, grid_height=5)

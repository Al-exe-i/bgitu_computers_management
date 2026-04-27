from collections.abc import Sequence

from core.exceptions import AudienceGridValidationError
from models import Hardware
from schemas.hardware import HardwareGridItem
from utils.hw_specs import validate_specs


class GridHelper:
    @staticmethod
    def rectangles_intersect(a: HardwareGridItem, b: HardwareGridItem) -> bool:
        return not (
                a.x + a.width <= b.x or
                b.x + b.width <= a.x or
                a.y + a.height <= b.y or
                b.y + b.height <= a.y
        )

    @staticmethod
    def validate_item_bounds(item: HardwareGridItem, grid_width: int, grid_height: int) -> None:
        if item.x < 0 or item.y < 0:
            raise AudienceGridValidationError("Hardware coordinates must be non-negative")

        if item.x + item.width > grid_width:
            raise AudienceGridValidationError(
                f"Hardware id={item.id or 'new'} exceeds audience width: "
                f"x={item.x}, width={item.width}, audience_width={grid_width}"
            )

        if item.y + item.height > grid_height:
            raise AudienceGridValidationError(
                f"Hardware id={item.id or 'new'} exceeds audience height: "
                f"y={item.y}, height={item.height}, audience_height={grid_height}"
            )

    @staticmethod
    def validate_grid(items: Sequence[HardwareGridItem], grid_width: int, grid_height: int) -> None:
        seen_ids: set[int] = set()

        for item in items:
            GridHelper.validate_item_bounds(item, grid_width, grid_height)

            if item.id is not None:
                if item.id in seen_ids:
                    raise AudienceGridValidationError(f"Duplicate hardware id={item.id} in payload")
                seen_ids.add(item.id)

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if GridHelper.rectangles_intersect(items[i], items[j]):
                    raise AudienceGridValidationError(
                        f"Hardware items intersect: "
                        f"{items[i].id or 'new'} and {items[j].id or 'new'}"
                    )

    @staticmethod
    def apply_grid_item(db_item: Hardware, item: HardwareGridItem) -> None:
        db_item.x = item.x
        db_item.y = item.y
        db_item.width = item.width
        db_item.height = item.height
        db_item.type = item.type
        db_item.state = item.state
        db_item.description = item.description
        db_item.inv_number = item.inv_number
        db_item.title = item.title
        db_item.specs = validate_specs(item.type, item.specs)

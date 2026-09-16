from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.inventory.types import RoomType


class RoomPlacement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audience_public_id: UUID
    x: int = Field(ge=0, le=49, strict=True)
    y: int = Field(ge=0, le=49, strict=True)
    width: int = Field(ge=1, le=50, strict=True)
    height: int = Field(ge=1, le=50, strict=True)


class FloorLandmarks(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    north: str = Field(default="", max_length=128)
    south: str = Field(default="", max_length=128)
    west: str = Field(default="", max_length=128)
    east: str = Field(default="", max_length=128)


class FloorInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)


class FloorPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0, strict=True)
    width: int = Field(ge=1, le=50, strict=True)
    height: int = Field(ge=1, le=50, strict=True)
    rooms: list[RoomPlacement] = Field(max_length=400)
    landmarks: FloorLandmarks = Field(default_factory=FloorLandmarks)

    @model_validator(mode="after")
    def validate_layout(self):
        ids = set()
        occupied = set()
        for room in self.rooms:
            if room.audience_public_id in ids:
                raise ValueError("Кабинет указан в схеме повторно")
            ids.add(room.audience_public_id)
            if room.x + room.width > self.width or room.y + room.height > self.height:
                raise ValueError("Кабинет выходит за границы этажа")
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    if (x, y) in occupied:
                        raise ValueError("Кабинеты не должны пересекаться")
                    occupied.add((x, y))
        return self


class FloorRoom(BaseModel):
    audience_public_id: UUID
    number: int
    room_type: RoomType
    description: str | None
    placement: RoomPlacement | None = None


class FloorPlanResponse(BaseModel):
    office_id: int
    floor: int
    width: int
    height: int
    revision: int
    rooms: list[FloorRoom]
    landmarks: FloorLandmarks = Field(default_factory=FloorLandmarks)

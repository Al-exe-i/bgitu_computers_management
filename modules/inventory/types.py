from enum import Enum, StrEnum


class RoomType(StrEnum):
    educational = "educational"
    administrative = "administrative"


class HardwareType(Enum):
    computer = "computer"
    tv = "tv"
    projector = "projector"
    printer = "printer"
    switch = "switch"
    router = "router"
    server = "server"
    other = "other"

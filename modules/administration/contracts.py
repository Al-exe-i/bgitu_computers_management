from collections.abc import Iterator
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class ProtectedFile:
    content: Iterator[bytes]
    filename: str
    media_type: str

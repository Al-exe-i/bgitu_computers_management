from collections.abc import Iterator, Sequence
from typing import Any, Protocol


class AuditLogReaderPort(Protocol):
    async def list(self, **kwargs: Any) -> tuple[Sequence[Any], int]: ...


class ProtectedObjectStoragePort(Protocol):
    def exists(self, key: str) -> bool: ...
    def iter_range(self, key: str) -> Iterator[bytes]: ...

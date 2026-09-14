from collections.abc import Iterator
from typing import Any, Protocol

from modules.administration.schemas import AuditLogItem


class AuditLogReaderPort(Protocol):
    async def list(self, **kwargs: Any) -> tuple[list[AuditLogItem], int]: ...


class ProtectedObjectStoragePort(Protocol):
    def exists(self, key: str) -> bool: ...
    def iter_range(self, key: str) -> Iterator[bytes]: ...

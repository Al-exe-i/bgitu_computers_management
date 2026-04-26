from typing import Any, Protocol


class AuditLogger(Protocol):
    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ) -> Any: ...


class IdentityActor(Protocol):
    id: int
    role: Any
    is_superuser: bool
    password: str
